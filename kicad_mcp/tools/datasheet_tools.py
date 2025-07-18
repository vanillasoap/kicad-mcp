"""Datasheet-related MCP tools (uConfig wrapper).

Currently provides one public tool:

    extract_symbol_from_pdf(url: str, *, progress_callback) -> {
        "symbol_file": "/abs/path/out.kicad_sym",
        "pin_table": [...],
    }

It downloads the PDF to a temporary directory, invokes **uConfig** to parse the
pin-table and generate a KiCad symbol, then returns the absolute path of the
symbol file along with the extracted pin metadata.

The tool adheres to the canonical MCP *envelope* pattern and re-uses the same
error taxonomy employed by *supplier_tools*.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable, Dict, List, Any

import aiohttp

_ERROR_TYPES = {
    "NetworkError",
    "ParseError",
    "Timeout",
    "MissingTool",
}

_ResultEnvelope = Dict[str, object]

_PROGRESS_INTERVAL = 0.5
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20.0)

UCONFIG_BIN = os.getenv("UCONFIG_BIN", "uconfig")


class DatasheetError(Exception):
    def __init__(self, err_type: str, msg: str):
        if err_type not in _ERROR_TYPES:
            err_type = "ParseError"
        self.err_type = err_type
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _envelope_ok(result, start: float) -> _ResultEnvelope:
    return {"ok": True, "result": result, "elapsed_s": time.perf_counter() - start}


def _envelope_err(err_type: str, msg: str, start: float) -> _ResultEnvelope:
    if err_type not in _ERROR_TYPES:
        err_type = "ParseError"
    return {
        "ok": False,
        "error": {"type": err_type, "message": msg},
        "elapsed_s": time.perf_counter() - start,
    }


async def _periodic_progress(cancel: asyncio.Event, cb: Callable[[float, str], None], msg: str):
    pct = 0.0
    while not cancel.is_set():
        try:
            maybe = cb(pct, msg)
            if asyncio.iscoroutine(maybe):
                await maybe
        except Exception:
            pass
        pct = (pct + 4.0) % 100.0
        await asyncio.sleep(_PROGRESS_INTERVAL)


async def _download_pdf(url: str, dest: Path):
    try:
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as sess:
            async with sess.get(url) as resp:
                if resp.status != 200:
                    raise DatasheetError("NetworkError", f"HTTP {resp.status}")
                data = await resp.read()
                dest.write_bytes(data)
    except asyncio.TimeoutError as te:
        raise DatasheetError("Timeout", "download timed out") from te
    except DatasheetError:
        raise
    except Exception as exc:
        raise DatasheetError("NetworkError", str(exc)) from exc


async def _run_uconfig(pdf_path: Path, out_dir: Path, timeout: float = 30.0) -> Path:
    if shutil.which(UCONFIG_BIN) is None:
        raise DatasheetError("MissingTool", "uconfig executable not found; install and/or set UCONFIG_BIN")

    proc = await asyncio.create_subprocess_exec(
        UCONFIG_BIN,
        "--output",
        str(out_dir),
        str(pdf_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise DatasheetError("Timeout", "uconfig processing timed out")

    if proc.returncode != 0:
        stderr = (await proc.stderr.read()).decode(errors="ignore") if proc.stderr else "uconfig failed"
        raise DatasheetError("ParseError", stderr.strip())

    # uConfig usually writes <part>.kicad_sym in output dir
    syms = list(out_dir.glob("*.kicad_sym"))
    if not syms:
        raise DatasheetError("ParseError", "symbol file not produced by uconfig")
    return syms[0]


# ---------------------------------------------------------------------------
# Public MCP tool
# ---------------------------------------------------------------------------

from mcp.server.fastmcp import FastMCP  # late import to avoid heavy deps

_mcp_instance: FastMCP | None = None


async def extract_symbol_from_pdf(  # noqa: D401
    url: str,
    *,
    progress_callback: Callable[[float, str], None],
) -> _ResultEnvelope:
    """Download *url* PDF and run uConfig, returning symbol path + pin table."""
    start = time.perf_counter()
    cancel = asyncio.Event()
    spinner = asyncio.create_task(_periodic_progress(cancel, progress_callback, "parsing pdf"))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        pdf_file = tmp_dir / "source.pdf"
        try:
            await _download_pdf(url, pdf_file)
            sym_path = await _run_uconfig(pdf_file, tmp_dir)
            # uConfig may emit pinout.json; if not available, return empty list
            pin_json = next(iter(tmp_dir.glob("*pin*.json")), None)
            pin_table: List[Dict[str, Any]] = []
            if pin_json and pin_json.exists():
                try:
                    pin_table = json.loads(pin_json.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pin_table = []
            cancel.set()
            await spinner
            return _envelope_ok({"symbol_file": str(sym_path.resolve()), "pin_table": pin_table}, start)
        except DatasheetError as de:
            cancel.set()
            await spinner
            return _envelope_err(de.err_type, str(de), start)
        except Exception as exc:  # pragma: no cover
            cancel.set()
            await spinner
            return _envelope_err("ParseError", str(exc), start)


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_datasheet_tools(mcp: FastMCP) -> None:  # noqa: D401
    global _mcp_instance
    _mcp_instance = mcp

    async def _stub(*args, **kwargs):  # type: ignore[override]
        return await extract_symbol_from_pdf(*args, **kwargs)

    _stub.__name__ = extract_symbol_from_pdf.__name__
    _stub.__doc__ = extract_symbol_from_pdf.__doc__
    mcp.tool()(_stub)
