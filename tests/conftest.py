from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Generator
from contextlib import closing, contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO_APP = ROOT / "demo" / "app.py"
SMOKE_APP = Path(__file__).resolve().parent / "smoke_app.py"


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _drain(proc: subprocess.Popen[str], sink: list[str]) -> None:
    """
    Continuously read the server's output.

    Without this the pipe buffer fills and the server blocks mid-test. Gradio
    also prints a line per custom-component file request, so this is not
    hypothetical.
    """
    assert proc.stdout is not None
    for line in proc.stdout:
        sink.append(line)


def _wait_for_port(
    host: str,
    port: int,
    proc: subprocess.Popen[str],
    output: list[str],
    timeout: float = 60.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Fail immediately on a crashed server rather than burning the timeout.
        if proc.poll() is not None:
            raise RuntimeError(
                f"Server exited with code {proc.returncode} before listening.\n"
                f"--- server output ---\n{''.join(output)}"
            )
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((host, port))
                return
            except OSError:
                time.sleep(0.25)
    raise TimeoutError(
        f"Server on {host}:{port} did not come up within {timeout}s.\n"
        f"--- server output ---\n{''.join(output)}"
    )


@contextmanager
def _serve(script: Path) -> Generator[str, None, None]:
    """Start a Gradio script on a random port and yield its URL."""
    port = _free_port()
    env = os.environ.copy()
    env["GRADIO_SERVER_PORT"] = str(port)
    env["GRADIO_SERVER_NAME"] = "127.0.0.1"
    env["GRADIO_ANALYTICS_ENABLED"] = "False"

    proc = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output: list[str] = []
    reader = threading.Thread(target=_drain, args=(proc, output), daemon=True)
    reader.start()

    try:
        _wait_for_port("127.0.0.1", port, proc, output)
        yield f"http://127.0.0.1:{port}/"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        reader.join(timeout=5)
        # Surface server output so a failure isn't debugged blind.
        if output:
            sys.stderr.write("\n--- server output ---\n")
            sys.stderr.write("".join(output))
            sys.stderr.write("\n--- end server output ---\n")


@pytest.fixture(scope="session")
def serve_app() -> Callable[[Path], object]:
    """Factory so a test can launch whichever app it needs."""
    return _serve


@pytest.fixture(scope="session")
def smoke_url() -> Generator[str, None, None]:
    """The test-owned app: no pre-set value, so it needs no network."""
    with _serve(SMOKE_APP) as url:
        yield url


@pytest.fixture(scope="session")
def demo_url() -> Generator[str, None, None]:
    """The real demo app, which pre-populates from a remote URL."""
    with _serve(DEMO_APP) as url:
        yield url
