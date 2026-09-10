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

    def test_igg_report_saved_and_isolated_from_ige(self, admin_session, seed_records):
        codes = [seed_records[0]["dnlab_code"], seed_records[1]["dnlab_code"]]
        names = {seed_records[0]["name"], seed_records[1]["name"]}
        payload = self._payload({
            "report_type": "igg",
            "allergen_codes": codes,
        })
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["report_type"] == "igg"
        assert rep["allergen_codes"] == codes
        snap_codes = [a["dnlab_code"] for a in rep["allergens"]]
        assert snap_codes == codes
        assert {a["name"] for a in rep["allergens"]} == names
        assert all(a.get("type") == "IgG specifiche" for a in rep["allergens"])
        agg = rep["aggregation"]
        assert agg["total"] == 2
        assert len(agg["codes"]) == 1
        assert agg["codes"][0]["siss_code"] == "0090685"
        assert agg["codes"][0]["description"] == "IGG SPECIFICHE ALLERGOLOGICHE"
        assert agg["codes"][0]["quantity"] == 2
        assert "0090681.00" not in {c["siss_code"] for c in agg["codes"]}
        assert "molecular_count" not in agg

        r2 = admin_session.get(f"{BASE_URL}/api/reports/{rep['report_id']}", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["report_type"] == "igg"

        listed = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        found = next(x for x in listed if x["report_id"] == rep["report_id"])
        assert found["report_type"] == "igg"

        r3 = admin_session.delete(f"{BASE_URL}/api/reports/{rep['report_id']}", timeout=15)
        assert r3.status_code == 200
        r4 = admin_session.get(f"{BASE_URL}/api/reports/{rep['report_id']}", timeout=15)
        assert r4.status_code == 404

    def test_igg_invalid_code_returns_400_and_creates_nothing(self, admin_session, seed_records):
        valid = seed_records[0]["dnlab_code"]
        marker = f"TEST_IGG_BAD_{uuid.uuid4().hex[:8]}"
        payload = self._payload({
            "report_type": "igg",
            "allergen_codes": [valid, "dnlab_inesistente_xyz"],
            "patient": {"first_name": marker, "last_name": "Rossi", "dob": "1990-01-01"},
        })
        before = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 400, r.text
        assert "Uno o più codici IgG selezionati non sono validi" in r.text
        after = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert len(after) == len(before)
        assert all(doc.get("patient", {}).get("first_name") != marker for doc in after)

    def test_igg_duplicate_code_returns_400_and_creates_nothing(self, admin_session, seed_records):
        valid = seed_records[0]["dnlab_code"]
        marker = f"TEST_IGG_DUP_{uuid.uuid4().hex[:8]}"
        payload = self._payload({
            "report_type": "igg",
            "allergen_codes": [valid, valid],
            "patient": {"first_name": marker, "last_name": "Rossi", "dob": "1990-01-01"},
        })
        before = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 400, r.text
        assert "La selezione IgG contiene codici duplicati" in r.text
        after = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert len(after) == len(before)
        assert all(doc.get("patient", {}).get("first_name") != marker for doc in after)

    def test_invalid_report_type_422(self, admin_session):
        payload = self._payload({"report_type": "invalid"})
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 422


class TestReportUpdate:
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

    def test_put_ige_updates_same_id(self, admin_session):
        created = admin_session.post(
            f"{BASE_URL}/api/reports", json=self._payload({"report_type": "ige"}), timeout=15
        )
        assert created.status_code == 200, created.text
        orig = created.json()
        report_id = orig["report_id"]
        created_at = orig["created_at"]
        payload = self._payload({
            "report_type": "ige",
            "allergen_codes": ["f1", "f2", "f3"],
            "notes": "updated",
        })
        r = admin_session.put(f"{BASE_URL}/api/reports/{report_id}", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["report_id"] == report_id
        assert rep["created_at"] == created_at
        assert "updated_at" in rep and rep["updated_at"]
        assert rep["allergen_codes"] == ["f1", "f2", "f3"]
        assert rep["aggregation"] != orig["aggregation"]
        assert rep["notes"] == "updated"
        listed = admin_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert sum(1 for x in listed if x["report_id"] == report_id) == 1
        admin_session.delete(f"{BASE_URL}/api/reports/{report_id}", timeout=15)

    def test_put_igg_updates_snapshot_and_quantity(self, admin_session, seed_records):
        codes2 = [seed_records[0]["dnlab_code"], seed_records[1]["dnlab_code"]]
        codes1 = [seed_records[0]["dnlab_code"]]
        created = admin_session.post(
            f"{BASE_URL}/api/reports",
            json=self._payload({"report_type": "igg", "allergen_codes": codes2}),
            timeout=15,
        )
        assert created.status_code == 200, created.text
        orig = created.json()
        report_id = orig["report_id"]
        created_at = orig["created_at"]
        r = admin_session.put(
            f"{BASE_URL}/api/reports/{report_id}",
            json=self._payload({"report_type": "igg", "allergen_codes": codes1}),
            timeout=15,
        )
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["report_id"] == report_id
        assert rep["created_at"] == created_at
        assert "updated_at" in rep
        assert rep["report_type"] == "igg"
        assert [a["dnlab_code"] for a in rep["allergens"]] == codes1
        assert rep["aggregation"]["total"] == 1
        assert rep["aggregation"]["codes"][0]["siss_code"] == "0090685"
        assert rep["aggregation"]["codes"][0]["quantity"] == 1
        assert "molecular_count" not in rep["aggregation"]
        admin_session.delete(f"{BASE_URL}/api/reports/{report_id}", timeout=15)

    def test_put_missing_report_404(self, admin_session):
        r = admin_session.put(
            f"{BASE_URL}/api/reports/rep_doesnotexist",
            json=self._payload({"report_type": "ige"}),
            timeout=15,
        )
        assert r.status_code == 404

    def test_put_cannot_change_ige_to_igg(self, admin_session, seed_records):
        created = admin_session.post(
            f"{BASE_URL}/api/reports", json=self._payload({"report_type": "ige"}), timeout=15
        ).json()
        r = admin_session.put(
            f"{BASE_URL}/api/reports/{created['report_id']}",
            json=self._payload({
                "report_type": "igg",
                "allergen_codes": [seed_records[0]["dnlab_code"]],
            }),
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "Non è possibile cambiare il tipo di un report esistente" in r.text
        admin_session.delete(f"{BASE_URL}/api/reports/{created['report_id']}", timeout=15)

    def test_put_cannot_change_igg_to_ige(self, admin_session, seed_records):
        created = admin_session.post(
            f"{BASE_URL}/api/reports",
            json=self._payload({
                "report_type": "igg",
                "allergen_codes": [seed_records[0]["dnlab_code"]],
            }),
            timeout=15,
        ).json()
        r = admin_session.put(
            f"{BASE_URL}/api/reports/{created['report_id']}",
            json=self._payload({"report_type": "ige", "allergen_codes": ["f1", "f2"]}),
            timeout=15,
        )
        assert r.status_code == 400, r.text
        assert "Non è possibile cambiare il tipo di un report esistente" in r.text
        admin_session.delete(f"{BASE_URL}/api/reports/{created['report_id']}", timeout=15)

    def test_put_igg_invalid_and_duplicate_codes_400(self, admin_session, seed_records):
        valid = seed_records[0]["dnlab_code"]
        created = admin_session.post(
            f"{BASE_URL}/api/reports",
            json=self._payload({"report_type": "igg", "allergen_codes": [valid]}),
            timeout=15,
        ).json()
        report_id = created["report_id"]
        r_dup = admin_session.put(
            f"{BASE_URL}/api/reports/{report_id}",
            json=self._payload({"report_type": "igg", "allergen_codes": [valid, valid]}),
            timeout=15,
        )
        assert r_dup.status_code == 400
        assert "La selezione IgG contiene codici duplicati" in r_dup.text
        r_bad = admin_session.put(
            f"{BASE_URL}/api/reports/{report_id}",
            json=self._payload({
                "report_type": "igg",
                "allergen_codes": [valid, "dnlab_inesistente_xyz"],
            }),
            timeout=15,
        )
        assert r_bad.status_code == 400
        assert "Uno o più codici IgG selezionati non sono validi" in r_bad.text
        still = admin_session.get(f"{BASE_URL}/api/reports/{report_id}", timeout=15).json()
        assert still["allergen_codes"] == [valid]
        admin_session.delete(f"{BASE_URL}/api/reports/{report_id}", timeout=15)
