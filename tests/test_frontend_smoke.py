"""
Frontend smoke test.

The motivation is bundled-runtime drift across Gradio versions: a pre-built
component bundle encodes how it reaches Gradio's Svelte runtime, and a wheel
built for one Gradio generation 404s when served by another. Gradio 6.9 moved
that runtime into the component itself. Those 404s are what the asset checks
below catch, and a component that fails to mount never renders an <img>.
"""

from __future__ import annotations

import socket
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest
from playwright.sync_api import (
    ConsoleMessage,
    Locator,
    Page,
    Request,
    Response,
    sync_playwright,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_TIFF = ROOT / "demo" / "data" / "sample.tiff"

ASSET_SUFFIXES = (".js", ".css", ".mjs")
ASSET_PATH_HINTS = ("/assets/", "/static/", "/svelte/", "/file=")
REMOTE_EXAMPLE_HOST = "raw.githubusercontent.com"


def _is_asset(url: str) -> bool:
    if any(url.endswith(suf) or f"{suf}?" in url for suf in ASSET_SUFFIXES):
        return True
    return any(hint in url for hint in ASSET_PATH_HINTS)


def _has_internet(host: str = REMOTE_EXAMPLE_HOST, port: int = 443) -> bool:
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except OSError:
        return False


class PageWatcher:
    """Collects the failure signals we assert on at the end of a test."""

    def __init__(self) -> None:
        self.console_errors: list[str] = []
        self.failed_requests: list[str] = []
        self.bad_asset_responses: list[str] = []
        self.requested_urls: list[str] = []

    def attach(self, page: Page) -> None:
        page.on("console", self._on_console)
        page.on("request", lambda req: self.requested_urls.append(req.url))
        page.on("requestfailed", self._on_request_failed)
        page.on("response", self._on_response)

    def _on_console(self, msg: ConsoleMessage) -> None:
        if msg.type == "error":
            self.console_errors.append(msg.text)

    def _on_request_failed(self, req: Request) -> None:
        if _is_asset(req.url):
            self.failed_requests.append(f"{req.method} {req.url} :: {req.failure}")

    def _on_response(self, resp: Response) -> None:
        if resp.status >= 400 and _is_asset(resp.url):
            self.bad_asset_responses.append(f"{resp.status} {resp.url}")

    def assert_clean(self) -> None:
        assert not self.console_errors, "console errors:\n" + "\n".join(
            self.console_errors
        )
        assert not self.failed_requests, "failed asset requests:\n" + "\n".join(
            self.failed_requests
        )
        assert not self.bad_asset_responses, "HTTP >=400 on assets:\n" + "\n".join(
            self.bad_asset_responses
        )


@contextmanager
def open_page(url: str) -> Generator[tuple[Page, PageWatcher], None, None]:
    watcher = PageWatcher()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_context().new_page()
            watcher.attach(page)
            # `load` (not `networkidle`): Gradio keeps an SSE queue open.
            page.goto(url, wait_until="load", timeout=45_000)
            yield page, watcher
        finally:
            browser.close()


def assert_renders_image(block: Locator, where: str, timeout: int = 30_000) -> None:
    """
    Wait for the viewer to settle, then require that it settled on an image.

    Waiting on `img, .error-text` rather than just `img` matters: the two are
    mutually exclusive template branches, so waiting only for `img` and then
    asserting no `.error-text` can never fail -- it just times out with a much
    worse message when the component errors.
    """
    block.locator(".image-wrapper img, .image-wrapper .error-text").first.wait_for(
        timeout=timeout
    )
    errors = block.locator(".image-wrapper .error-text")
    if errors.count():
        pytest.fail(f"{where}: viewer showed an error instead of an image")
    assert block.locator(".image-wrapper img").count() == 1, (
        f"{where}: expected exactly one rendered image"
    )


@pytest.mark.skipif(
    not SAMPLE_TIFF.exists(), reason=f"sample TIFF not found at {SAMPLE_TIFF}"
)
def test_upload_and_round_trip_render(smoke_url: str) -> None:
    """
    Upload a local TIFF, then submit it and check the output side renders too.

    Requires no network: the app starts with no value, and the sample comes off
    disk. That is deliberate -- this asserts the component can render without
    internet access, which it could not while the decoder came from a CDN.
    """
    with open_page(smoke_url) as (page, watcher):
        page.wait_for_selector(".gradio-tiff-block", timeout=20_000)
        blocks = page.locator(".gradio-tiff-block")

        input_block = blocks.first
        input_block.locator(".gradio-tiff-upload").wait_for(timeout=10_000)
        input_block.locator('input[type="file"]').first.set_input_files(
            str(SAMPLE_TIFF)
        )
        assert_renders_image(input_block, "input after upload")

        # Round-trip through Python: postprocess -> /file= -> decode -> render.
        page.get_by_role("button", name="Submit").click()
        assert_renders_image(blocks.last, "output after submit")

        remote = [u for u in watcher.requested_urls if REMOTE_EXAMPLE_HOST in u]
        assert not remote, f"test unexpectedly hit the network: {remote}"

    watcher.assert_clean()


@pytest.mark.network
@pytest.mark.skipif(not _has_internet(), reason="no internet access")
def test_demo_app_renders_remote_example(demo_url: str) -> None:
    """
    The real demo pre-populates its input from a GitHub raw URL.

    Covers the remote-URL branch of postprocess, which the offline test above
    cannot reach. Skipped when there is no connectivity.
    """
    with open_page(demo_url) as (page, watcher):
        page.wait_for_selector(".gradio-tiff-block", timeout=20_000)
        assert_renders_image(
            page.locator(".gradio-tiff-block").first, "demo initial mount"
        )

    watcher.assert_clean()
