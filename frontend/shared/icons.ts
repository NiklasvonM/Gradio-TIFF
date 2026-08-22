// Inline SVG paths used by the component, mirroring the subset of icons we used
// to import from @gradio/icons. Kept as raw `<path d="...">` strings so the
// .svelte components can drop them straight into a small <svg> wrapper.

export const DOWNLOAD_PATH =
    "M12 3v12m0 0l-4-4m4 4l4-4M5 21h14";

export const CLEAR_PATH =
    "M6 6l12 12M18 6L6 18";

export const IMAGE_PATH =
    "M4 4h16v16H4z M8 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M20 16l-5-5-10 9";

export const UPLOAD_PATH =
    "M12 21V9m0 0l-4 4m4-4l4 4M5 3h14";
