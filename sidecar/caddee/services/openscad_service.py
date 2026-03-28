"""OpenSCAD CLI wrapper — compiles .scad source to STL via the openscad binary."""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class CompileResult:
    """Outcome of an OpenSCAD compile attempt."""

    success: bool
    stl_path: str | None
    error: str | None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_scad(scad_code: str, *, timeout: int = 60) -> CompileResult:
    """Write *scad_code* to a temp file, compile to STL, return the result.

    The STL is written to a persistent temp file (not auto-deleted) so that
    downstream consumers (Phase 3 FreeCAD) can access it by path.

    Parameters
    ----------
    scad_code:
        Complete OpenSCAD source code.
    timeout:
        Maximum seconds to wait for the OpenSCAD process.

    Returns
    -------
    CompileResult with success flag, optional STL path, and optional error.
    """
    # Write the .scad source to a temp file.
    scad_file = tempfile.NamedTemporaryFile(
        suffix=".scad", delete=False, mode="w", encoding="utf-8",
    )
    scad_file.write(scad_code)
    scad_file.flush()
    scad_file.close()

    # Prepare the output STL path (persistent temp file).
    stl_fd = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    stl_path = stl_fd.name
    stl_fd.close()

    try:
        result = subprocess.run(
            ["openscad", "-o", stl_path, scad_file.name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        _cleanup(scad_file.name)
        _cleanup(stl_path)
        return CompileResult(
            success=False,
            stl_path=None,
            error="openscad binary not found. Is OpenSCAD installed and on PATH?",
        )
    except subprocess.TimeoutExpired:
        _cleanup(scad_file.name)
        _cleanup(stl_path)
        return CompileResult(
            success=False,
            stl_path=None,
            error=f"OpenSCAD compilation timed out after {timeout}s.",
        )

    # Clean up the source file — we only need the STL.
    _cleanup(scad_file.name)

    # OpenSCAD returns 0 on success.  Anything else is a compile error.
    if result.returncode != 0:
        _cleanup(stl_path)
        error_text = result.stderr.strip() or result.stdout.strip() or "Unknown OpenSCAD error"
        return CompileResult(success=False, stl_path=None, error=error_text)

    # Verify the STL file was actually created and is non-empty.
    stl = Path(stl_path)
    if not stl.exists() or stl.stat().st_size == 0:
        _cleanup(stl_path)
        error_text = result.stderr.strip() or "OpenSCAD produced an empty STL file."
        return CompileResult(success=False, stl_path=None, error=error_text)

    return CompileResult(success=True, stl_path=stl_path, error=None)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cleanup(path: str) -> None:
    """Silently remove a file if it exists."""
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
