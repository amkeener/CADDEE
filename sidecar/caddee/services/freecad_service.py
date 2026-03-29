"""FreeCAD integration service — mesh analysis (trimesh) and CAD export (FreeCAD).

FreeCAD ships its own Python (3.11) which differs from the sidecar's Python.
All FreeCAD operations are executed via subprocess using FreeCAD's bundled Python.
"""

from __future__ import annotations

import base64
import json
import logging
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FreeCAD detection — locate the .app bundle and its bundled Python
# ---------------------------------------------------------------------------

_FREECAD_APP_PATHS = [
    Path("/Applications/FreeCAD.app"),
    Path.home() / "Applications" / "FreeCAD.app",
]

_freecad_python: Path | None = None
_freecad_lib: Path | None = None
_freecad_available: bool | None = None


def _detect_freecad() -> bool:
    """Locate FreeCAD's bundled Python and lib directory. Cache the result."""
    global _freecad_available, _freecad_python, _freecad_lib
    if _freecad_available is not None:
        return _freecad_available

    for app_path in _FREECAD_APP_PATHS:
        python = app_path / "Contents" / "Resources" / "bin" / "python"
        lib = app_path / "Contents" / "Resources" / "lib"
        if python.exists() and (lib / "FreeCAD.so").exists():
            _freecad_python = python
            _freecad_lib = lib
            _freecad_available = True
            logger.info("FreeCAD found: %s (python: %s)", app_path, python)
            return True

    _freecad_available = False
    logger.info("FreeCAD not found — STEP/FCStd operations disabled")
    return False


def is_freecad_available() -> bool:
    """Return whether FreeCAD is installed and its Python is accessible."""
    return _detect_freecad()


def _run_freecad_script(script: str, timeout: float = 30.0) -> dict:
    """Execute a Python script using FreeCAD's bundled Python.

    The script must print a single JSON line to stdout as its result.
    Returns the parsed JSON dict, or {"error": "..."} on failure.
    """
    if not _freecad_python or not _freecad_lib:
        return {"error": "FreeCAD Python not available"}

    # Prepend sys.path setup so FreeCAD modules are importable
    wrapper = f"""
import sys, json
sys.path.insert(0, {str(_freecad_lib)!r})
try:
{_indent(script, 4)}
except Exception as _exc:
    print(json.dumps({{"error": str(_exc)}}))
"""
    try:
        proc = subprocess.run(
            [str(_freecad_python), "-c", wrapper],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # Find the last JSON line in stdout (FreeCAD may print warnings)
        for line in reversed(proc.stdout.strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        # No JSON found
        stderr = proc.stderr.strip()[-500:] if proc.stderr else ""
        return {"error": f"No JSON output from FreeCAD script. stderr: {stderr}"}
    except subprocess.TimeoutExpired:
        return {"error": "FreeCAD operation timed out"}
    except Exception as e:
        return {"error": f"Failed to run FreeCAD script: {e}"}


def _indent(text: str, spaces: int) -> str:
    """Indent every line of text by *spaces* spaces."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class CompatibilityCheck:
    """Single check result."""

    name: str
    passed: bool
    severity: str  # "info" | "warning" | "error"
    message: str


@dataclass
class CompatibilityResult:
    """Full mesh analysis result."""

    checks: list[CompatibilityCheck] = field(default_factory=list)
    stats: dict[str, float | int | str] = field(default_factory=dict)
    overall: str = "unknown"  # "pass" | "warning" | "fail"

    def to_dict(self) -> dict:
        return {
            "checks": [
                {"name": c.name, "passed": c.passed, "severity": c.severity, "message": c.message}
                for c in self.checks
            ],
            "stats": self.stats,
            "overall": self.overall,
        }


@dataclass
class ExportResult:
    """Result of a CAD export operation."""

    success: bool
    output_path: str | None
    error: str | None

    def to_dict(self) -> dict:
        return {"success": self.success, "outputPath": self.output_path, "error": self.error}


@dataclass
class ImportResult:
    """Result of importing a CAD file."""

    success: bool
    file_type: str  # "stl" | "scad" | "step" | "fcstd"
    scad_code: str | None = None
    stl_base64: str | None = None
    metadata: dict = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "fileType": self.file_type,
            "scadCode": self.scad_code,
            "stlBase64": self.stl_base64,
            "metadata": self.metadata,
            "error": self.error,
        }


@dataclass
class Capabilities:
    """Reports what features are available."""

    trimesh_available: bool = True
    freecad_available: bool = False
    mesh_analysis: bool = True
    step_export: bool = False
    fcstd_export: bool = False
    live_sync: bool = False

    def to_dict(self) -> dict:
        return {
            "trimeshAvailable": self.trimesh_available,
            "freecadAvailable": self.freecad_available,
            "meshAnalysis": self.mesh_analysis,
            "stepExport": self.step_export,
            "fcstdExport": self.fcstd_export,
            "liveSync": self.live_sync,
        }


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


def get_capabilities() -> Capabilities:
    """Report which features are available based on installed dependencies."""
    has_fc = is_freecad_available()
    return Capabilities(
        trimesh_available=True,
        freecad_available=has_fc,
        mesh_analysis=True,
        step_export=has_fc,
        fcstd_export=has_fc,
        live_sync=has_fc,
    )


# ---------------------------------------------------------------------------
# Mesh analysis (trimesh — always available)
# ---------------------------------------------------------------------------


def analyze_mesh(stl_base64: str) -> CompatibilityResult:
    """Run compatibility checks on an STL mesh using trimesh.

    Parameters
    ----------
    stl_base64:
        Base64-encoded STL binary data.

    Returns
    -------
    CompatibilityResult with individual checks, stats, and overall verdict.
    """
    result = CompatibilityResult()

    try:
        stl_bytes = base64.b64decode(stl_base64)
    except Exception as e:
        result.checks.append(
            CompatibilityCheck("decode", False, "error", f"Failed to decode STL data: {e}")
        )
        result.overall = "fail"
        return result

    # Write to temp file for trimesh to load
    tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    tmp.write(stl_bytes)
    tmp.flush()
    tmp.close()

    try:
        mesh = trimesh.load(tmp.name, force="mesh")
    except Exception as e:
        result.checks.append(
            CompatibilityCheck("load", False, "error", f"Failed to load STL mesh: {e}")
        )
        result.overall = "fail"
        Path(tmp.name).unlink(missing_ok=True)
        return result
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    # --- Watertight check ---
    is_watertight = bool(mesh.is_watertight)
    result.checks.append(
        CompatibilityCheck(
            "watertight",
            is_watertight,
            "info" if is_watertight else "warning",
            "Mesh is watertight (fully enclosed) — good for 3D printing and STEP export."
            if is_watertight
            else "Mesh is not watertight — it has holes or open edges. This may cause issues with STEP export and 3D printing.",
        )
    )

    # --- Manifold edges check ---
    # Non-manifold edges are shared by more than 2 faces
    edges = mesh.edges_sorted
    unique_edges, edge_counts = np.unique(edges, axis=0, return_counts=True)
    non_manifold_count = int(np.sum(edge_counts > 2))
    is_manifold = non_manifold_count == 0
    result.checks.append(
        CompatibilityCheck(
            "manifold",
            is_manifold,
            "info" if is_manifold else "error",
            "All edges are manifold (shared by exactly 2 faces)."
            if is_manifold
            else f"Found {non_manifold_count} non-manifold edges (shared by 3+ faces). This geometry is invalid for most CAD operations.",
        )
    )

    # --- Degenerate faces check ---
    # Faces with zero area
    face_areas = mesh.area_faces
    degenerate_count = int(np.sum(face_areas < 1e-10))
    no_degenerate = degenerate_count == 0
    result.checks.append(
        CompatibilityCheck(
            "degenerate_faces",
            no_degenerate,
            "info" if no_degenerate else "warning",
            "No degenerate (zero-area) faces found."
            if no_degenerate
            else f"Found {degenerate_count} degenerate faces with near-zero area. These may cause rendering or export issues.",
        )
    )

    # --- Consistent winding check ---
    is_consistent = bool(mesh.is_winding_consistent)
    result.checks.append(
        CompatibilityCheck(
            "winding",
            is_consistent,
            "info" if is_consistent else "warning",
            "Face normals are consistently oriented."
            if is_consistent
            else "Face normals are inconsistently oriented (some faces appear inside-out). This can cause rendering artifacts.",
        )
    )

    # --- Volume check (only meaningful for watertight meshes) ---
    if is_watertight:
        volume = float(mesh.volume)
        if volume <= 0:
            result.checks.append(
                CompatibilityCheck(
                    "volume",
                    False,
                    "warning",
                    "Mesh has non-positive volume — normals may be inverted.",
                )
            )
        else:
            result.checks.append(
                CompatibilityCheck(
                    "volume",
                    True,
                    "info",
                    f"Volume: {volume:.2f} cubic units.",
                )
            )

    # --- Thin wall detection (via face-to-face proximity) ---
    # Approximate: check if any vertices are very close to non-adjacent faces
    # Use the mesh's minimum edge length as a proxy for thin features
    edge_lengths = mesh.edges_unique_length
    if len(edge_lengths) > 0:
        min_edge = float(np.min(edge_lengths))
        median_edge = float(np.median(edge_lengths))
        thin_threshold = median_edge * 0.05  # 5% of median edge length
        thin_edge_count = int(np.sum(edge_lengths < thin_threshold))
        has_thin_features = thin_edge_count > 0
        result.checks.append(
            CompatibilityCheck(
                "thin_features",
                not has_thin_features,
                "info" if not has_thin_features else "warning",
                "No extremely thin features detected."
                if not has_thin_features
                else f"Found {thin_edge_count} edges shorter than {thin_threshold:.4f} units (5% of median edge length). Very thin features may fail to print or export.",
            )
        )
    # --- Stats ---
    result.stats = {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "surfaceArea": round(float(mesh.area), 4),
        "boundingBox": [round(float(x), 4) for x in mesh.bounding_box.extents],
    }
    if is_watertight:
        result.stats["volume"] = round(float(mesh.volume), 4)

    # --- Overall verdict ---
    severities = [c.severity for c in result.checks]
    if "error" in severities:
        result.overall = "fail"
    elif "warning" in severities:
        result.overall = "warning"
    else:
        result.overall = "pass"

    return result


# ---------------------------------------------------------------------------
# STEP / FCStd export (FreeCAD — optional)
# ---------------------------------------------------------------------------


def export_step(stl_base64: str, output_path: str) -> ExportResult:
    """Convert STL to STEP format using FreeCAD (via subprocess)."""
    if not is_freecad_available():
        return ExportResult(
            success=False,
            output_path=None,
            error="FreeCAD is not installed. Install FreeCAD 1.0+ to enable STEP export.",
        )

    # Write STL to temp file
    stl_bytes = base64.b64decode(stl_base64)
    tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    tmp.write(stl_bytes)
    tmp.flush()
    tmp.close()

    result = _run_freecad_script(f"""
import Part
shape = Part.Shape()
shape.read({tmp.name!r})
solid = Part.makeSolid(shape)
solid.exportStep({output_path!r})
print(json.dumps({{"success": True, "outputPath": {output_path!r}}}))
""")
    Path(tmp.name).unlink(missing_ok=True)

    if "error" in result and result.get("error"):
        return ExportResult(success=False, output_path=None, error=f"STEP export failed: {result['error']}")
    return ExportResult(success=True, output_path=output_path, error=None)


def export_fcstd(stl_base64: str, output_path: str, label: str = "CADDEE_Model") -> ExportResult:
    """Convert STL to FreeCAD document (.FCStd) format (via subprocess)."""
    if not is_freecad_available():
        return ExportResult(
            success=False,
            output_path=None,
            error="FreeCAD is not installed. Install FreeCAD 1.0+ to enable FCStd export.",
        )

    stl_bytes = base64.b64decode(stl_base64)
    tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    tmp.write(stl_bytes)
    tmp.flush()
    tmp.close()

    result = _run_freecad_script(f"""
import FreeCAD
import Mesh
doc = FreeCAD.newDocument("CADDEE")
mesh_obj = doc.addObject("Mesh::Feature", {label!r})
mesh_obj.Mesh = Mesh.Mesh({tmp.name!r})
doc.recompute()
doc.saveAs({output_path!r})
FreeCAD.closeDocument(doc.Name)
print(json.dumps({{"success": True, "outputPath": {output_path!r}}}))
""")
    Path(tmp.name).unlink(missing_ok=True)

    if "error" in result and result.get("error"):
        return ExportResult(success=False, output_path=None, error=f"FCStd export failed: {result['error']}")
    return ExportResult(success=True, output_path=output_path, error=None)


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

_IMPORT_DIR = Path.home() / ".caddee" / "imports"


def _ensure_import_workspace() -> Path:
    """Create and return the persistent import workspace directory."""
    _IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    return _IMPORT_DIR


def _generate_import_scad(stl_path: Path, mesh: trimesh.Trimesh) -> str:
    """Generate an OpenSCAD wrapper that imports the STL and documents its dimensions.

    This lets Claude modify the imported design using boolean operations
    (difference, union, intersection) around the imported mesh.
    """
    bounds = mesh.bounding_box.extents
    centroid = mesh.centroid
    return (
        f"// Imported model: {stl_path.name}\n"
        f"// Bounding box: {bounds[0]:.2f} x {bounds[1]:.2f} x {bounds[2]:.2f}\n"
        f"// Centroid: [{centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f}]\n"
        f"// Vertices: {len(mesh.vertices)}, Faces: {len(mesh.faces)}\n"
        f"//\n"
        f"// To modify this model, wrap it in boolean operations:\n"
        f"//   difference() {{ imported_model(); your_cut_geometry(); }}\n"
        f"//   union() {{ imported_model(); your_added_geometry(); }}\n"
        f"\n"
        f"$fn = 64;\n"
        f"\n"
        f"module imported_model() {{\n"
        f'    import("{stl_path}");\n'
        f"}}\n"
        f"\n"
        f"imported_model();\n"
    )


# ---------------------------------------------------------------------------
# Import files
# ---------------------------------------------------------------------------


def import_file(file_path: str) -> ImportResult:
    """Import a CAD file and extract usable data.

    Supported formats: .stl, .scad, .step/.stp, .FCStd
    """
    path = Path(file_path)
    if not path.exists():
        return ImportResult(success=False, file_type="unknown", error=f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".scad":
        return _import_scad(path)
    elif suffix == ".stl":
        return _import_stl(path)
    elif suffix in (".step", ".stp"):
        return _import_step(path)
    elif suffix == ".fcstd":
        return _import_fcstd(path)
    else:
        return ImportResult(
            success=False,
            file_type="unknown",
            error=f"Unsupported file format: {suffix}. Supported: .stl, .scad, .step, .stp, .FCStd",
        )


def _import_scad(path: Path) -> ImportResult:
    """Import an OpenSCAD source file."""
    try:
        scad_code = path.read_text(encoding="utf-8")
        return ImportResult(
            success=True,
            file_type="scad",
            scad_code=scad_code,
            metadata={"fileName": path.name, "size": path.stat().st_size},
        )
    except Exception as e:
        return ImportResult(success=False, file_type="scad", error=f"Failed to read .scad file: {e}")


def _import_stl(path: Path) -> ImportResult:
    """Import an STL file — copy to workspace, generate OpenSCAD wrapper, return base64."""
    try:
        # Copy STL to persistent workspace so OpenSCAD import() path stays valid
        workspace = _ensure_import_workspace()
        dest = workspace / path.name
        stl_bytes = path.read_bytes()
        dest.write_bytes(stl_bytes)
        stl_b64 = base64.b64encode(stl_bytes).decode("ascii")

        # Basic stats via trimesh
        mesh = trimesh.load(str(path), force="mesh")
        metadata = {
            "fileName": path.name,
            "size": path.stat().st_size,
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
        }

        # Generate OpenSCAD wrapper so Claude can modify the imported mesh
        scad_code = _generate_import_scad(dest, mesh)

        return ImportResult(
            success=True,
            file_type="stl",
            scad_code=scad_code,
            stl_base64=stl_b64,
            metadata=metadata,
        )
    except Exception as e:
        return ImportResult(success=False, file_type="stl", error=f"Failed to read STL file: {e}")


def _import_step(path: Path) -> ImportResult:
    """Import a STEP file via FreeCAD subprocess — convert to STL, generate OpenSCAD wrapper."""
    if not is_freecad_available():
        return ImportResult(
            success=False,
            file_type="step",
            error="FreeCAD is required to import STEP files. Install FreeCAD 1.0+.",
        )

    # Save the converted STL into the import workspace
    workspace = _ensure_import_workspace()
    dest = workspace / (path.stem + ".stl")

    result = _run_freecad_script(f"""
import base64, FreeCAD, Part, Mesh
shape = Part.Shape()
shape.read({str(path)!r})
doc = FreeCAD.newDocument("Import")
part_obj = doc.addObject("Part::Feature", "Imported")
part_obj.Shape = shape
doc.recompute()
Mesh.export([doc.getObject("Imported")], {str(dest)!r})
FreeCAD.closeDocument(doc.Name)
stl_bytes = open({str(dest)!r}, "rb").read()
stl_b64 = base64.b64encode(stl_bytes).decode("ascii")
print(json.dumps({{"success": True, "stlBase64": stl_b64}}))
""", timeout=60.0)

    if "error" in result and result.get("error"):
        return ImportResult(success=False, file_type="step", error=f"Failed to import STEP: {result['error']}")

    stl_b64 = result.get("stlBase64", "")

    # Generate OpenSCAD wrapper from the converted STL
    scad_code = None
    if dest.exists():
        try:
            mesh = trimesh.load(str(dest), force="mesh")
            scad_code = _generate_import_scad(dest, mesh)
        except Exception as e:
            logger.warning("Could not generate OpenSCAD wrapper for STEP import: %s", e)

    return ImportResult(
        success=True,
        file_type="step",
        scad_code=scad_code,
        stl_base64=stl_b64,
        metadata={"fileName": path.name, "size": path.stat().st_size},
    )


def _import_fcstd(path: Path) -> ImportResult:
    """Import a FreeCAD document via subprocess — extract mesh as STL, generate OpenSCAD wrapper."""
    if not is_freecad_available():
        return ImportResult(
            success=False,
            file_type="fcstd",
            error="FreeCAD is required to import .FCStd files. Install FreeCAD 1.0+.",
        )

    workspace = _ensure_import_workspace()
    dest = workspace / (path.stem + ".stl")

    result = _run_freecad_script(f"""
import base64, FreeCAD, Mesh
doc = FreeCAD.openDocument({str(path)!r})
objects = doc.Objects
if not objects:
    print(json.dumps({{"error": "FreeCAD document contains no objects."}}))
else:
    Mesh.export(objects, {str(dest)!r})
    stl_bytes = open({str(dest)!r}, "rb").read()
    stl_b64 = base64.b64encode(stl_bytes).decode("ascii")
    obj_count = len(objects)
    FreeCAD.closeDocument(doc.Name)
    print(json.dumps({{"success": True, "stlBase64": stl_b64, "objectCount": obj_count}}))
""", timeout=60.0)

    if "error" in result and result.get("error"):
        return ImportResult(success=False, file_type="fcstd", error=f"Failed to import FCStd: {result['error']}")

    stl_b64 = result.get("stlBase64", "")

    scad_code = None
    if dest.exists():
        try:
            mesh = trimesh.load(str(dest), force="mesh")
            scad_code = _generate_import_scad(dest, mesh)
        except Exception as e:
            logger.warning("Could not generate OpenSCAD wrapper for FCStd import: %s", e)

    return ImportResult(
        success=True,
        file_type="fcstd",
        scad_code=scad_code,
        stl_base64=stl_b64,
        metadata={
            "fileName": path.name,
            "size": path.stat().st_size,
            "objectCount": result.get("objectCount", 0),
        },
    )


# ---------------------------------------------------------------------------
# Live sync — push STEP to running FreeCAD instance
# ---------------------------------------------------------------------------

_FREECAD_SOCKET_PORT = 12345  # Default FreeCAD remote scripting port


def check_freecad_running(host: str = "127.0.0.1", port: int = _FREECAD_SOCKET_PORT) -> bool:
    """Check if a FreeCAD instance is listening for remote scripting."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((host, port))
        sock.close()
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def live_sync_push(
    stl_base64: str,
    host: str = "127.0.0.1",
    port: int = _FREECAD_SOCKET_PORT,
    label: str = "CADDEE_Live",
) -> ExportResult:
    """Push current model to a running FreeCAD instance via socket scripting.

    FreeCAD must be running with the remote scripting server enabled:
        FreeCAD > Edit > Preferences > General > Macro > Run macros in local environment
        Then start server: FreeCAD.Console.PrintMessage("Starting server")

    This sends a Python script over the socket that imports the STL.
    """
    if not check_freecad_running(host, port):
        return ExportResult(
            success=False,
            output_path=None,
            error=f"No FreeCAD instance found at {host}:{port}. Start FreeCAD and enable remote scripting.",
        )

    try:
        # Write STL to temp file that FreeCAD can access
        stl_bytes = base64.b64decode(stl_base64)
        tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
        tmp.write(stl_bytes)
        tmp.flush()
        tmp.close()

        # Python script to execute inside FreeCAD
        script = f"""
import Mesh
import FreeCAD

# Remove previous CADDEE object if it exists
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("CADDEE")
for obj in doc.Objects:
    if obj.Label.startswith("{label}"):
        doc.removeObject(obj.Name)

# Import new mesh
mesh_obj = doc.addObject("Mesh::Feature", "{label}")
mesh_obj.Mesh = Mesh.Mesh("{tmp.name}")
doc.recompute()
FreeCADGui.ActiveDocument.ActiveView.fitAll()
"""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        sock.sendall(script.encode("utf-8"))
        sock.close()

        return ExportResult(success=True, output_path=tmp.name, error=None)
    except Exception as e:
        return ExportResult(
            success=False, output_path=None, error=f"Live sync failed: {e}"
        )
