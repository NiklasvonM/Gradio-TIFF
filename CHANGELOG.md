# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-22

### Changed

- Require `gradio>=6.9`. Gradio 6.9 replaced the shared Svelte runtime chunks with one shipped inside the component, so this build cannot mount on Gradio 6.0-6.8. Use 0.1.2 there.
- Reject non-TIFF files.
- Ship the TIFF decoder with the component instead of fetching it from a CDN, so the component works offline and under a strict CSP.
- Replace `@gradio/atoms`, `@gradio/icons`, `@gradio/upload` and `@gradio/statustracker` with local Svelte components.
- Unpin `svelte`, which is now bundled into the component.

### Fixed

- Fix the component never mounting on Gradio 6.9 and newer.
- Fix the generated API reference showing every parameter's default as `value = None`.
- Show an error instead of an endless spinner when the TIFF decoder fails to load.
- Reject non-TIFF files before uploading them, and report upload failures in the UI.
- Fix a stale render overwriting a newer one when values change quickly.
- Revoke object URLs created for the non-TIFF fallback.

### Added

- Playwright smoke test covering upload, render and the round trip through Python.
- CI matrix running the smoke test against several Gradio versions weekly.
- `ruff`, `mypy` and `tsc` checks, run in CI.
