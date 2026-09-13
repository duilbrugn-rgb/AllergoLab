"""Static checks: no clinical persistence and no doctor_name in the runtime flow."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / "backend"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_server_has_no_reports_api():
    src = _read(BACKEND / "server.py")
    assert "@api_router.post(\"/reports\")" not in src
    assert "@api_router.get(\"/reports\")" not in src
    assert "@api_router.put(\"/reports/{report_id}\")" not in src
    assert "@api_router.delete(\"/reports/{report_id}\")" not in src
    assert "class PatientInfo" not in src
    assert "class ReportInput" not in src
    assert "doctor_name" not in src
    assert "db.reports" not in src
    assert "purge-old-reports" not in src


def test_frontend_has_no_reports_calls():
    hits = []
    for path in FRONTEND_SRC.rglob("*"):
        if path.suffix not in {".js", ".jsx"}:
            continue
        if path.name.endswith(".test.js"):
            continue
        text = path.read_text(encoding="utf-8")
        if "/reports" in text or "doctor_name" in text or "doctorName" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_purge_script_exists_and_defaults_to_dry_run():
    script = _read(BACKEND / "purge_reports_collection.py")
    assert "--execute" in script
    assert "dry-run" in script.lower()
    assert "count_documents" in script
