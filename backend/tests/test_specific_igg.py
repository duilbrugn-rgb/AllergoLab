"""Tests for specific IgG catalog and report_type phase-1 behaviour."""
import json
import os
import uuid
from pathlib import Path

import pytest
import requests

REQUIRED_FIELDS = ("dnlab_code", "name", "type", "siss_code", "siss_description")
JSON_PATH = Path(__file__).resolve().parent.parent / "specific_igg.json"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _backend_url():
    value = os.environ.get("REACT_APP_BACKEND_URL")
    if value:
        return value.rstrip("/")
    for env_path in (
        Path("/app/frontend/.env"),
        REPO_ROOT / "frontend" / ".env",
    ):
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        return line.split("=", 1)[1].strip().rstrip("/")
        except OSError:
            continue
    return "http://localhost:8000"


def _admin_credential(key):
    value = os.environ.get(key)
    if value:
        return value
    for env_path in (
        Path("/app/backend/.env"),
        REPO_ROOT / "backend" / ".env",
    ):
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith(key + "="):
                        return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return ""


BASE_URL = _backend_url()
ADMIN_EMAIL = _admin_credential("ADMIN_EMAIL")
ADMIN_PASSWORD = _admin_credential("ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def seed_records():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    return data


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


class TestSpecificIggDataset:
    def test_exactly_25_records(self, seed_records):
        assert len(seed_records) == 25

    def test_dnlab_codes_unique(self, seed_records):
        codes = [row["dnlab_code"] for row in seed_records]
        assert len(codes) == len(set(codes))

    def test_required_fields(self, seed_records):
        for row in seed_records:
            for key in REQUIRED_FIELDS:
                assert key in row and row[key], f"missing {key} in {row}"

    def test_type_is_igg_specifiche(self, seed_records):
        assert all(row["type"] == "IgG specifiche" for row in seed_records)

    def test_siss_code(self, seed_records):
        assert all(row["siss_code"] == "0090685" for row in seed_records)

    def test_siss_description(self, seed_records):
        assert all(
            row["siss_description"] == "IGG SPECIFICHE ALLERGOLOGICHE"
            for row in seed_records
        )


class TestSpecificIggApi:
    def test_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/specific-igg", timeout=15)
        assert r.status_code == 401

    def test_authenticated_returns_25(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/specific-igg", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 25
        codes = [row["dnlab_code"] for row in data]
        assert codes == sorted(codes)


class TestIgeUnchanged:
    def test_aggregate_ige_unchanged(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/aggregate", json={"codes": ["f1", "d1"]}, timeout=15
        )
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["total"] == 2
        codes = {c["siss_code"]: c for c in j["codes"]}
        assert "0090681.00" in codes
        assert codes["0090681.00"]["quantity"] == 2


class TestReportType:
    def _payload(self, extra=None):
        payload = {
            "patient": {
                "first_name": f"TEST_{uuid.uuid4().hex[:8]}",
                "last_name": "Rossi",
                "dob": "1990-01-01",
            },
            "doctor_name": "Dr TEST",
            "allergen_codes": ["f1", "f2"],
            "notes": "test notes",
            "letterhead": "",
        }
        if extra:
            payload.update(extra)
        return payload

    def test_missing_report_type_saved_as_ige(self, admin_session):
        payload = self._payload()
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["report_type"] == "ige"
        report_id = rep["report_id"]
        r2 = admin_session.get(f"{BASE_URL}/api/reports/{report_id}", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["report_type"] == "ige"
        admin_session.delete(f"{BASE_URL}/api/reports/{report_id}", timeout=15)

    def test_explicit_ige_saved_as_ige(self, admin_session):
        payload = self._payload({"report_type": "ige"})
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["report_type"] == "ige"
        admin_session.delete(f"{BASE_URL}/api/reports/{rep['report_id']}", timeout=15)

    def test_igg_returns_501_and_creates_nothing(self, admin_session):
        marker = f"TEST_IGG_{uuid.uuid4().hex[:8]}"
        payload = self._payload({
            "report_type": "igg",
            "patient": {"first_name": marker, "last_name": "Rossi", "dob": "1990-01-01"},
        })
        before = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 501, r.text
        assert "Il salvataggio dei report IgG sarà implementato nella fase successiva" in r.text
        after = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert len(after) == len(before)
        assert all(doc.get("patient", {}).get("first_name") != marker for doc in after)

    def test_invalid_report_type_422(self, admin_session):
        payload = self._payload({"report_type": "invalid"})
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 422
