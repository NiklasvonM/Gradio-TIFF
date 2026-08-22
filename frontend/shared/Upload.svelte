<script lang="ts">
    // Minimal upload widget. Replaces @gradio/upload to avoid coupling to
    // Gradio's frontend internals. The actual upload call is passed in as a
    // function prop (typically `gradio.shared.client.upload`), so this component
    // does not import from @gradio/client at runtime.
    import type { Snippet } from "svelte";
    import type { FileData } from "@gradio/client";
    import Icon from "./Icon.svelte";
    import { UPLOAD_PATH } from "./icons";

    // Gradio's `client.upload` does not take raw File objects. It takes
    // FileData-shaped entries with a `.blob` field (the actual File) plus the
    // metadata it later spreads into the response. `@gradio/client` ships a
    // `prepare_files` helper that does this wrapping; we replicate it inline so
    // we don't have to import another @gradio/* package at runtime.
    type PreparedFile = {
        path: string;
        orig_name: string;
        blob: File;
        size: number;
        mime_type: string;
    };

    interface Props {
        upload: (
            files: PreparedFile[],
            root: string,
            upload_id?: string,
        ) => Promise<(FileData | null)[] | null>;
        root: string;
        accept?: string;
        uploading?: boolean;
        on_load: (file: FileData) => void;
        /**
         * Checked before the file is uploaded. Return an error message to reject
         * the file, or null to accept it. `accept` only filters the file picker
         * dialog; drag-and-drop bypasses it entirely, so this is what actually
         * enforces the file type.
         */
        validate?: (file: File) => string | null;
        children?: Snippet;
    }

    let {
        upload,
        root,
        accept = "*",
        uploading = $bindable(false),
        on_load,
        validate,
        children,
    }: Props = $props();

    let dragging = $state(false);
    let error: string | null = $state(null);
    let input_el: HTMLInputElement | undefined = $state(undefined);

    function prepare(f: File): PreparedFile {
        return {
            path: f.name,
            orig_name: f.name,
            blob: f,
            size: f.size,
            mime_type: f.type,
        };
    }

    async function handle_files(files: FileList | File[] | null) {
        if (!files || files.length === 0) return;
        error = null;

        const selected = Array.from(files);
        if (validate) {
            const rejection = selected.map(validate).find((msg) => msg !== null);
            if (rejection) {
                error = rejection;
                return;
            }
        }

        uploading = true;
        try {
            const uploaded = await upload(selected.map(prepare), root);
            const first = uploaded?.[0];
            if (first) on_load(first);
            else error = "Upload did not return a file.";
        } catch (e) {
            error = e instanceof Error ? e.message : "Upload failed.";
            console.error("Upload failed:", e);
        } finally {
            uploading = false;
        }
    }

    function on_drop(e: DragEvent) {
        e.preventDefault();
        dragging = false;
        handle_files(e.dataTransfer?.files ?? null);
    }

    function on_dragover(e: DragEvent) {
        e.preventDefault();
        if (!dragging) dragging = true;
    }

    function on_dragleave(e: DragEvent) {
        if (e.currentTarget === e.target) dragging = false;
    }

    function on_change(e: Event) {
        const target = e.target as HTMLInputElement;
        handle_files(target.files);
        target.value = "";
    }

    function on_click() {
        input_el?.click();
    }

    function on_keydown(e: KeyboardEvent) {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            input_el?.click();
        }
    }
</script>

<div
    class="gradio-tiff-upload"
    class:dragging
    class:uploading
    role="button"
    tabindex="0"
    aria-label="Upload TIFF file"
    onclick={on_click}
    onkeydown={on_keydown}
    ondrop={on_drop}
    ondragover={on_dragover}
    ondragleave={on_dragleave}
>
    <input
        bind:this={input_el}
        type="file"
        {accept}
        onchange={on_change}
        hidden
    />
    <div class="upload-content">
        <Icon path={UPLOAD_PATH} size={32} />
        <div class="text">
            {#if uploading}
                <span>Uploading…</span>
            {:else if error}
                <span class="upload-error" role="alert">{error}</span>
            {:else if children}
                {@render children()}
            {:else}
                <span>Drop a TIFF file here, or click to browse.</span>
            {/if}
        </div>
    </div>
</div>

<style>
    .gradio-tiff-upload {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        min-height: 200px;
        padding: var(--spacing-lg, 16px);
        background: var(--background-fill-secondary);
        border: 2px dashed var(--border-color-primary);
        border-radius: var(--radius-lg);
        cursor: pointer;
        color: var(--body-text-color-subdued, var(--body-text-color));
        transition:
            background 0.15s ease,
            border-color 0.15s ease;
    }
    .gradio-tiff-upload:hover,
    .gradio-tiff-upload:focus-visible,
    .gradio-tiff-upload.dragging {
        background: var(--background-fill-primary);
        border-color: var(--color-accent, var(--body-text-color));
        outline: none;
    }
    .gradio-tiff-upload.uploading {
        opacity: 0.7;
        cursor: progress;
    }
    .upload-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        font-family: var(--font-sans);
    }
    .text {
        text-align: center;
        font-size: var(--text-sm, 0.875rem);
    }
    .upload-error {
        color: var(--color-red-500, #ef4444);
    }
</style>
