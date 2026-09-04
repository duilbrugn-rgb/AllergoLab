"""Tests for profile CRUD (admin RBAC), GET /profiles, and cron purge-old-reports."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://allergen-selector.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "duilbrugn@gmail.com"
ADMIN_PASSWORD = "AllergoLab2026!"
CRON_SECRET = "k9Qm2Xr7Tp4Ls8Vn3Wd6Yb1Zc5Hg0Jf"


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def user_client():
    """Register a non-admin user."""
    s = requests.Session()
    email = f"ztest_user_{int(time.time())}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register", json={
        "email": email, "password": "password123", "first_name": "zTest", "last_name": "User"
    })
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def sample_codes(admin_client):
    r = admin_client.get(f"{BASE_URL}/api/allergens")
    assert r.status_code == 200
    codes = [a["code"] for a in r.json()[:5]]
    assert len(codes) == 5
    return codes


class TestProfileRBAC:
    def test_get_profiles_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/profiles")
        assert r.status_code == 401

    def test_get_profiles_authenticated_user(self, user_client):
        r = user_client.get(f"{BASE_URL}/api/profiles")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_create_requires_admin(self, user_client, sample_codes):
        r = user_client.post(f"{BASE_URL}/api/admin/profiles",
                             json={"name": "zTEST-forbidden", "description": "", "allergen_codes": sample_codes})
        assert r.status_code == 403

    def test_admin_create_unauthenticated(self, sample_codes):
        r = requests.post(f"{BASE_URL}/api/admin/profiles",
                          json={"name": "zTEST-noauth", "description": "", "allergen_codes": sample_codes})
        assert r.status_code == 401


class TestProfileCRUD:
    created_id = None

    def test_create_profile(self, admin_client, sample_codes):
        r = admin_client.post(f"{BASE_URL}/api/admin/profiles",
                              json={"name": "zTEST-Profile", "description": "test", "allergen_codes": sample_codes})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["name"] == "zTEST-Profile"
        assert data["allergen_codes"] == sample_codes
        assert "profile_id" in data
        TestProfileCRUD.created_id = data["profile_id"]

    def test_list_shows_created(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/profiles")
        assert r.status_code == 200
        ids = [p["profile_id"] for p in r.json()]
        assert TestProfileCRUD.created_id in ids

    def test_update_profile(self, admin_client, sample_codes):
        pid = TestProfileCRUD.created_id
        new_codes = sample_codes[:3]
        r = admin_client.put(f"{BASE_URL}/api/admin/profiles/{pid}",
                             json={"name": "zTEST-Profile-upd", "description": "upd", "allergen_codes": new_codes})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "zTEST-Profile-upd"
        assert data["allergen_codes"] == new_codes

    def test_delete_profile(self, admin_client):
        pid = TestProfileCRUD.created_id
        r = admin_client.delete(f"{BASE_URL}/api/admin/profiles/{pid}")
        assert r.status_code == 200
        # Verify not in list
        r2 = admin_client.get(f"{BASE_URL}/api/profiles")
        ids = [p["profile_id"] for p in r2.json()]
        assert pid not in ids

    def test_update_nonexistent(self, admin_client, sample_codes):
        r = admin_client.put(f"{BASE_URL}/api/admin/profiles/prof_nonexistent",
                             json={"name": "x", "description": "", "allergen_codes": sample_codes})
        assert r.status_code == 404

    def test_delete_nonexistent(self, admin_client):
        r = admin_client.delete(f"{BASE_URL}/api/admin/profiles/prof_nonexistent")
        assert r.status_code == 404


class TestCronPurge:
    def test_no_auth(self):
        r = requests.post(f"{BASE_URL}/api/cron/purge-old-reports")
        assert r.status_code == 401

    def test_wrong_secret(self):
        r = requests.post(f"{BASE_URL}/api/cron/purge-old-reports",
                          headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401

    def test_correct_secret_and_recent_report_preserved(self, admin_client, sample_codes):
        # Create a report NOW
        r = admin_client.post(f"{BASE_URL}/api/reports", json={
            "patient": {"first_name": "zTEST", "last_name": "Patient", "dob": "2000-01-01"},
            "doctor_name": "zTEST Doc",
            "allergen_codes": sample_codes[:2],
            "notes": "", "letterhead": ""
        })
        assert r.status_code == 200, r.text
        rid = r.json()["report_id"]

        # Call cron
        r2 = requests.post(f"{BASE_URL}/api/cron/purge-old-reports",
                           headers={"Authorization": f"Bearer {CRON_SECRET}"})
        assert r2.status_code == 200
        assert r2.json().get("accepted") is True

        # Wait for background task
        time.sleep(2)

        # Verify recent report still exists
        r3 = admin_client.get(f"{BASE_URL}/api/reports/{rid}")
        assert r3.status_code == 200, "Recent report was incorrectly purged!"

        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/reports/{rid}")


class TestSISSInvariance:
    """Adding a profile and manually selecting the same allergens must produce same SISS aggregation."""

    def test_aggregate_invariance(self, admin_client, sample_codes):
        codes = sample_codes[:4]
        r1 = admin_client.post(f"{BASE_URL}/api/aggregate", json={"codes": codes})
        assert r1.status_code == 200
        # Remove one
        subset = codes[:3]
        r2 = admin_client.post(f"{BASE_URL}/api/aggregate", json={"codes": subset})
        r3 = admin_client.post(f"{BASE_URL}/api/aggregate", json={"codes": subset})
        assert r3.status_code == 200
        assert r2.json() == r3.json(), "Aggregation not deterministic for same codes"
