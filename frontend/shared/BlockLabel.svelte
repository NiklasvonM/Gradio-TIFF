<script lang="ts">
    import Icon from "./Icon.svelte";

    interface Props {
        show_label?: boolean | null;
        label?: string | null;
        icon_path?: string;
    }

    let { show_label = true, label, icon_path }: Props = $props();
</script>

{#if show_label !== false && label}
    <div class="gradio-tiff-block-label">
        {#if icon_path}
            <span class="icon">
                <Icon path={icon_path} size={14} />
            </span>
        {/if}
        <span>{label}</span>
    </div>
{/if}

<style>
    .gradio-tiff-block-label {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        font-size: var(--text-sm, 0.875rem);
        color: var(--block-label-text-color, var(--body-text-color));
        background: var(--block-label-background-fill, transparent);
        border-radius: var(--radius-sm);
        margin-bottom: 8px;
        width: fit-content;
    }
    .icon {
        display: inline-flex;
    }
</style>
