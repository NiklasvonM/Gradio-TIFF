// tiff.js ships no type declarations (it is an Emscripten build of LibTIFF).
//
// This must stay an ambient declaration file: no top-level import/export, or the
// file becomes a module and `declare module` turns into an augmentation of an
// untyped module, which TypeScript rejects (TS2665). Use inline `import(...)`
// types instead.
declare module "tiff.js" {
    const Tiff: {
        initialize: (opts: { TOTAL_MEMORY: number }) => void;
        new (opts: { buffer: ArrayBuffer }): import("./types").TiffInstance;
    };
    export default Tiff;
}
