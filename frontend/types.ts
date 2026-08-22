import type { FileData } from "@gradio/client";

export interface TiffEvents {
    change: undefined;
    upload: undefined;
    clear: undefined;
}

export interface TiffProps {
    value: FileData | null;
    show_download_button?: boolean;
}

export interface TiffInstance {
    countDirectory: () => number;
    setDirectory: (index: number) => void;
    toCanvas: () => HTMLCanvasElement;
    close: () => void;
    width: () => number;
    height: () => number;
}

declare global {
    interface Window {
        Tiff: {
            initialize: (opts: { TOTAL_MEMORY: number }) => void;
            new (opts: { buffer: ArrayBuffer }): TiffInstance;
        };
    }
}
