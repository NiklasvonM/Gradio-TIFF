<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { Gradio } from "@gradio/utils";
    import type { FileData } from "@gradio/client";

    import Block from "./shared/Block.svelte";
    import BlockLabel from "./shared/BlockLabel.svelte";
    import IconButton from "./shared/IconButton.svelte";
    import EmptyState from "./shared/EmptyState.svelte";
    import Icon from "./shared/Icon.svelte";
    import Upload from "./shared/Upload.svelte";
    import {
        DOWNLOAD_PATH,
        CLEAR_PATH,
        IMAGE_PATH,
    } from "./shared/icons";

    import type { TiffEvents, TiffProps, TiffInstance } from "./types";

    // --- CONSTANTS ---
    const MEMORY_SIZE = 16777216 * 5; // ~80MB allocation for tiff.js

    // --- COMPONENT STATE ---
    const _props = $props();
    const gradio = new Gradio<TiffEvents, TiffProps>(_props);

    let value = $derived(gradio.props.value);
    let interactive = $derived(gradio.shared.interactive ?? true);

    let pages: string[] = $state([]);
    let page_index = $state(0);
    let uploading = $state(false);
    let lib_ready = $state(false);
    let lib_error = $state(false);
    let processing = $state(false);
    let current_processed_url: string | null = $state(null);

    // Object URLs we created for the non-TIFF fallback, so we can revoke them.
    // The normal path produces `data:` URLs, which need no cleanup.
    let object_urls: string[] = [];

    // Identifies the newest processTiff run. An older run that finishes late must
    // not overwrite the newer run's results.
    let process_seq = 0;

    // True between "we have a value" and "processTiff has finished trying".
    // Without this we briefly show the error state on first mount while the
    // tiff.js chunk is still loading. If the chunk failed outright, stop
    // pending so the error state can show instead of a permanent spinner.
    let pending = $derived(
        !!value &&
            !lib_error &&
            (!lib_ready || current_processed_url !== (value.url || value.path)),
    );

    // --- LIFECYCLE & EFFECTS ---

    onMount(async () => {
        try {
            await loadTiffLib();
            window.Tiff.initialize({ TOTAL_MEMORY: MEMORY_SIZE });
            lib_ready = true;
        } catch (e) {
            lib_error = true;
            console.error("Failed to load Tiff.js backend:", e);
        }
    });

    onDestroy(() => {
        replace_pages([]);
    });

    // Single place where `pages` is assigned, so revoking stays paired with it.
    function replace_pages(next: string[]): void {
        for (const url of object_urls) URL.revokeObjectURL(url);
        object_urls = next.filter((url) => url.startsWith("blob:"));
        pages = next;
    }

    $effect(() => {
        if (!value) {
            replace_pages([]);
            page_index = 0;
            current_processed_url = null;
            return;
        }

        const file_url = value.url || value.path;
        if (lib_ready && file_url && file_url !== current_processed_url) {
            processTiff(value);
        }
    });

    function isTiff(buffer: ArrayBuffer): boolean {
        if (buffer.byteLength < 4) return false;
        const view = new DataView(buffer);
        const magic = view.getUint16(0, false); // big endian
        // 0x4949 = "II" (Intel), 0x4D4D = "MM" (Motorola)
        return magic === 0x4949 || magic === 0x4d4d;
    }

    async function loadTiffLib(): Promise<void> {
        if (window.Tiff) return;

        // Dynamic import so the LibTIFF/Emscripten bundle (~3MB uncompressed)
        // becomes its own chunk, fetched from the component's own template
        // directory only when the component actually mounts. Previously this
        // came from a CDN, which made the component depend on public internet
        // access at render time.
        const mod = await import("tiff.js");

        // tiff.js is UMD. Under a Vite library build it normally takes its
        // `window.Tiff = Tiff` branch; if CommonJS interop kicks in instead, it
        // arrives as the module's default export. Accept either and normalise
        // onto window.Tiff so the rest of the component has one access path.
        if (!window.Tiff) {
            const ctor = mod.default ?? mod;
            if (typeof ctor !== "function")
                throw new Error("tiff.js did not expose a Tiff constructor");
            window.Tiff = ctor;
        }
    }

    async function processTiff(file: FileData) {
        if (!lib_ready || !window.Tiff) return;

        const url = file.url || file.path;
        if (!url) return;

        const seq = ++process_seq;
        processing = true;
        current_processed_url = url;

        let tiffInstance: TiffInstance | null = null;

        try {
            const response = await fetch(url);
            if (!response.ok)
                throw new Error(
                    `Network response was not ok: ${response.status}`,
                );

            const buffer = await response.arrayBuffer();
            if (seq !== process_seq) return;

            if (!isTiff(buffer)) {
                // Fallback: not a real TIFF (e.g. JPEG with .tif extension).
                // Let the browser render it directly.
                const blob = new Blob([buffer]);
                replace_pages([URL.createObjectURL(blob)]);
                page_index = 0;
                return;
            }

            tiffInstance = new window.Tiff({ buffer });

            let totalPages = 1;
            try {
                totalPages = tiffInstance.countDirectory();
            } catch (e) {
                console.warn(
                    "Could not read directory count, defaulting to 1 page.",
                    e,
                );
            }

            const new_pages: string[] = [];
            for (let i = 0; i < totalPages; i++) {
                try {
                    tiffInstance.setDirectory(i);
                    const canvas = tiffInstance.toCanvas();
                    if (canvas) {
                        new_pages.push(canvas.toDataURL("image/png"));
                    }
                } catch (e) {
                    console.warn(`Skipped corrupted page ${i}`, e);
                }
            }

            if (seq !== process_seq) return;
            replace_pages(new_pages);
            page_index = 0;
        } catch (error) {
            console.error("TIFF processing failed:", error);
            if (seq === process_seq) replace_pages([]);
        } finally {
            tiffInstance?.close();
            // A superseded run must not clear the newer run's loading state.
            if (seq === process_seq) processing = false;
        }
    }

    // --- EVENT HANDLERS ---

    // Runs before the file is sent to the server, so a wrong file type costs no
    // upload. Returns an error message, or null when the file is acceptable.
    // Content is validated separately in processTiff via the magic bytes, which
    // still lets a genuinely mislabelled image through to the browser fallback.
    function validate_tiff(file: File): string | null {
        const name = file.name.toLowerCase();
        const is_tiff =
            name.endsWith(".tif") ||
            name.endsWith(".tiff") ||
            file.type.includes("tiff");

        return is_tiff ? null : `Not a TIFF file: ${file.name}`;
    }

    function handle_upload(file: FileData) {
        gradio.props.value = file;
        gradio.dispatch("upload");
        gradio.dispatch("change");
    }

    function handle_clear() {
        gradio.props.value = null;
        gradio.dispatch("clear");
        gradio.dispatch("change");
    }
</script>

<Block
    visible={gradio.shared.visible}
    elem_id={gradio.shared.elem_id}
    elem_classes={gradio.shared.elem_classes}
>
    <BlockLabel
        show_label={gradio.shared.show_label}
        icon_path={IMAGE_PATH}
        label={gradio.shared.label || "TIFF Image"}
    />

    {#if !value}
        {#if interactive}
            <Upload
                upload={gradio.shared.client.upload}
                root={gradio.shared.root}
                accept="image/tiff,.tif,.tiff"
                validate={validate_tiff}
                bind:uploading
                on_load={handle_upload}
            />
        {:else}
            <EmptyState>
                <Icon path={IMAGE_PATH} size={48} />
            </EmptyState>
        {/if}
    {:else}
        <div class="tiff-viewer">
            {#if interactive}
                <div class="action-buttons">
                    <IconButton
                        path={CLEAR_PATH}
                        label="Clear"
                        onclick={handle_clear}
                    />
                </div>
            {/if}

            <div class="image-wrapper" class:loading={processing || pending}>
                {#if processing || pending}
                    <span class="loading-text">Rendering TIFF…</span>
                {:else if pages.length > 0}
                    <img
                        src={pages[page_index]}
                        alt={`Page ${page_index + 1}`}
                    />
                {:else}
                    <span class="error-text">Unable to render image</span>
                {/if}
            </div>

            <div class="controls-wrapper">
                {#if pages.length > 1}
                    <div class="nav-controls">
                        <button
                            class="nav-btn"
                            type="button"
                            onclick={() => page_index > 0 && page_index--}
                            disabled={page_index === 0}
                            aria-label="Previous page"
                        >
                            ←
                        </button>
                        <span class="page-count">
                            Page {page_index + 1} / {pages.length}
                        </span>
                        <button
                            class="nav-btn"
                            type="button"
                            onclick={() =>
                                page_index < pages.length - 1 && page_index++}
                            disabled={page_index === pages.length - 1}
                            aria-label="Next page"
                        >
                            →
                        </button>
                    </div>
                {:else}
                    <div></div>
                {/if}

                {#if gradio.props.show_download_button && value.url}
                    <IconButton
                        path={DOWNLOAD_PATH}
                        label="Download original"
                        href={value.url}
                        download={value.orig_name || "image.tiff"}
                    />
                {/if}
            </div>
        </div>
    {/if}
</Block>

<style>
    .tiff-viewer {
        display: flex;
        flex-direction: column;
        width: 100%;
        position: relative;
        gap: 0.5rem;
    }

    .image-wrapper {
        position: relative;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: var(--background-fill-secondary);
        border-radius: var(--radius-lg);
        overflow: hidden;
        min-height: 200px;
        border: 1px solid var(--border-color-primary);
    }

    .image-wrapper.loading {
        opacity: 0.7;
    }

    .loading-text,
    .error-text {
        color: var(--body-text-color-subdued);
        font-family: var(--font-sans);
    }

    .image-wrapper img {
        max-width: 100%;
        max-height: 70vh;
        object-fit: contain;
    }

    .controls-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        gap: 0.5rem;
        min-height: 36px;
    }

    .nav-controls {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        padding: 0.25rem 0.5rem;
        background: var(--background-fill-secondary);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color-primary);
        justify-content: center;
        margin: 0 auto;
    }

    .page-count {
        font-family: var(--font-mono);
        font-size: var(--text-sm);
        color: var(--body-text-color);
        min-width: 90px;
        text-align: center;
        user-select: none;
    }

    .nav-controls button.nav-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border: 1px solid var(--border-color-primary);
        border-radius: var(--radius-sm);
        cursor: pointer;
        background: var(--background-fill-primary);
        color: var(--body-text-color);
        transition: all 0.2s;
    }

    .nav-controls button.nav-btn:hover:not(:disabled) {
        background: var(--background-fill-secondary);
    }

    .nav-controls button.nav-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .action-buttons {
        position: absolute;
        top: 8px;
        right: 8px;
        z-index: 10;
    }
</style>
