<script lang="ts">
    import Icon from "./Icon.svelte";

    interface Props {
        path: string;
        label: string;
        onclick?: (e: MouseEvent) => void;
        href?: string;
        download?: string;
    }

    let { path, label, onclick, href, download }: Props = $props();
</script>

{#if href}
    <a
        class="gradio-tiff-icon-button"
        {href}
        {download}
        aria-label={label}
        title={label}
    >
        <Icon {path} {label} />
    </a>
{:else}
    <button
        type="button"
        class="gradio-tiff-icon-button"
        aria-label={label}
        title={label}
        {onclick}
    >
        <Icon {path} {label} />
    </button>
{/if}

<style>
    .gradio-tiff-icon-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        padding: 0;
        background: var(--background-fill-primary);
        color: var(--body-text-color);
        border: 1px solid var(--border-color-primary);
        border-radius: var(--radius-md);
        cursor: pointer;
        text-decoration: none;
        transition: background 0.15s ease;
    }
    .gradio-tiff-icon-button:hover {
        background: var(--background-fill-secondary);
        color: var(--color-accent, var(--body-text-color));
    }
    .gradio-tiff-icon-button:focus-visible {
        outline: 2px solid var(--color-accent, currentColor);
        outline-offset: 2px;
    }
</style>
