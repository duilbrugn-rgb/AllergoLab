"""Backend regression tests for AllergoLab."""
import os
import math
import json
import uuid
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/') if os.environ.get('REACT_APP_BACKEND_URL') else None
if BASE_URL is None:
    # Fallback: read frontend/.env
    with open('/app/frontend/.env') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BASE_URL = line.split('=', 1)[1].strip().rstrip('/')

ADMIN_EMAIL = "duilbrugn@gmail.com"
ADMIN_PASSWORD = "AllergoLab2026!"


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return s


# ---------- Auth ----------
class TestAuth:
    def test_admin_login_and_me(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r.status_code == 200
        u = r.json()
        assert u["email"] == ADMIN_EMAIL
        assert u["role"] == "admin"
        assert u["name"]

    def test_register_new_user_and_logout(self):
        s = requests.Session()
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        r = s.post(f"{BASE_URL}/api/auth/register",
                   json={"email": email, "password": "secret123",
                         "first_name": "Mario", "last_name": "Rossi"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == email
        assert data["name"] == "Mario Rossi"
        assert data["first_name"] == "Mario"
        # cookies set
        assert "access_token" in s.cookies.get_dict()
        # /me works
        r2 = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["email"] == email
        # logout
        r3 = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
        assert r3.status_code == 200
        # /me now fails
        s2 = requests.Session()  # fresh - cookies cleared
        r4 = s2.get(f"{BASE_URL}/api/auth/me", timeout=15)
        assert r4.status_code == 401

    def test_register_duplicate(self, admin_session):
        r = requests.post(f"{BASE_URL}/api/auth/register",
                          json={"email": ADMIN_EMAIL, "password": "AllergoLab2026!",
                                "first_name": "a", "last_name": "b"}, timeout=15)
        assert r.status_code == 400

    def test_login_invalid(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_google_session_missing_header(self):
        r = requests.post(f"{BASE_URL}/api/auth/google/session", timeout=15)
        assert r.status_code == 400

    def test_google_session_invalid_id(self):
        r = requests.post(f"{BASE_URL}/api/auth/google/session",
                          headers={"X-Session-ID": "invalid_" + uuid.uuid4().hex}, timeout=15)
        assert r.status_code in (401, 502)

    def test_allergens_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/allergens", timeout=15)
        assert r.status_code == 401


# ---------- Allergens ----------
class TestAllergens:
    def test_list_allergens(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/allergens", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 282, f"Expected 282 allergens, got {len(data)}"
        sample = data[0]
        for key in ("code", "name", "type", "siss_code", "siss_description"):
            assert key in sample, f"missing {key} in allergen"


# ---------- Aggregate ----------
class TestAggregate:
    def test_case_a_two_food_under5(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/aggregate", json={"codes": ["f1", "d1"]}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert j["total"] == 2
        codes = {c["siss_code"]: c for c in j["codes"]}
        assert "0090681.00" in codes
        assert codes["0090681.00"]["quantity"] == 2

    def test_case_b_six_foods(self, admin_session):
        codes = ["f1", "f2", "f3", "f4", "f5", "f6"]
        r = admin_session.post(f"{BASE_URL}/api/aggregate", json={"codes": codes}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        codes_map = {c["siss_code"]: c for c in j["codes"]}
        assert "0090687" in codes_map
        assert codes_map["0090687"]["quantity"] == 1

    def test_case_c_25_mixed_inal_alim(self, admin_session):
        # get 25 mixed inalanti + alimenti
        alls = admin_session.get(f"{BASE_URL}/api/allergens", timeout=20).json()
        inal = [a["code"] for a in alls if a["type"] == "Inalanti"][:13]
        alim = [a["code"] for a in alls if a["type"] == "Alimenti"][:12]
        codes = inal + alim
        assert len(codes) == 25
        r = admin_session.post(f"{BASE_URL}/api/aggregate", json={"codes": codes}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        cm = {c["siss_code"]: c for c in j["codes"]}
        assert "009068B" in cm
        assert cm["009068B"]["quantity"] == math.ceil(25 / 12) == 3

    def test_case_d_molecular(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/aggregate",
                               json={"codes": ["d202", "d203", "d205"]}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        cm = {c["siss_code"]: c for c in j["codes"]}
        assert "009068A" in cm
        # 3 molecular; but total<5 also triggers standard "0090681.00" for std (should be 0)
        assert cm["009068A"]["quantity"] == 3

    def test_case_e_65_allergens(self, admin_session):
        alls = admin_session.get(f"{BASE_URL}/api/allergens", timeout=20).json()
        # take first 65 non-molecular
        codes = [a["code"] for a in alls if a["type"] != "Allergeni molecolari"][:65]
        assert len(codes) == 65
        r = admin_session.post(f"{BASE_URL}/api/aggregate", json={"codes": codes}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        cm = {c["siss_code"]: c for c in j["codes"]}
        assert "009068D" in cm
        assert cm["009068D"]["quantity"] == 1


# ---------- Reports CRUD ----------
class TestReports:
    def test_create_list_get_delete(self, admin_session):
        payload = {
            "patient": {"first_name": "TEST_Pat", "last_name": "Rossi", "dob": "1990-01-01"},
            "doctor_name": "Dr TEST",
            "allergen_codes": ["f1", "f2"],
            "notes": "test notes",
            "letterhead": ""
        }
        r = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        rep = r.json()
        assert "report_id" in rep
        assert rep["patient"]["first_name"] == "TEST_Pat"
        assert "aggregation" in rep
        report_id = rep["report_id"]

        # list
        r2 = admin_session.get(f"{BASE_URL}/api/reports", timeout=15)
        assert r2.status_code == 200
        assert any(x["report_id"] == report_id for x in r2.json())

        # get single
        r3 = admin_session.get(f"{BASE_URL}/api/reports/{report_id}", timeout=15)
        assert r3.status_code == 200
        assert r3.json()["report_id"] == report_id

        # delete
        r4 = admin_session.delete(f"{BASE_URL}/api/reports/{report_id}", timeout=15)
        assert r4.status_code == 200

        # 404 after delete
        r5 = admin_session.get(f"{BASE_URL}/api/reports/{report_id}", timeout=15)
        assert r5.status_code == 404
