<script lang="ts">
    // Minimal block container. Mirrors enough of @gradio/atoms/Block for our needs
    // (visibility, elem_id/classes, padded container with theme-aware border)
    // without coupling to Gradio's internal Svelte runtime chunks.
    import type { Snippet } from "svelte";

    interface Props {
        visible?: boolean | "hidden";
        elem_id?: string;
        elem_classes?: string[] | string | null;
        padding?: boolean;
        children?: Snippet;
    }

    let {
        visible = true,
        elem_id,
        elem_classes,
        padding = true,
        children,
    }: Props = $props();

    let classes = $derived(
        Array.isArray(elem_classes)
            ? elem_classes.join(" ")
            : (elem_classes ?? ""),
    );

    let hidden = $derived(visible === false);
    let visually_hidden = $derived(visible === "hidden");
</script>

{#if !hidden}
    <div
        id={elem_id}
        class={`gradio-tiff-block ${classes}`}
        class:padded={padding}
        class:visually-hidden={visually_hidden}
    >
        {@render children?.()}
    </div>
{/if}

<style>
    .gradio-tiff-block {
        position: relative;
        display: flex;
        flex-direction: column;
        background: var(--block-background-fill, var(--background-fill-primary));
        border: var(--block-border-width, 1px) solid
            var(--block-border-color, var(--border-color-primary));
        border-radius: var(--block-radius, var(--radius-lg));
        color: var(--body-text-color);
    }
    .gradio-tiff-block.padded {
        padding: var(--block-padding, var(--spacing-lg));
    }
    .gradio-tiff-block.visually-hidden {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
        border: 0;
    }
</style>
