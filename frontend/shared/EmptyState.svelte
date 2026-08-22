<script lang="ts">
    import type { Snippet } from "svelte";

    interface Props {
        children?: Snippet;
    }
    let { children }: Props = $props();
</script>

<div class="gradio-tiff-empty">
    <div class="icon">
        {@render children?.()}
    </div>
</div>

<style>
    .gradio-tiff-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        width: 100%;
        background: var(--background-fill-secondary);
        border: 1px dashed var(--border-color-primary);
        border-radius: var(--radius-lg);
        color: var(--body-text-color-subdued);
    }
    .icon :global(svg) {
        width: 48px;
        height: 48px;
        opacity: 0.5;
    }
</style>
