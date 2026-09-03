"""RBAC admin CRUD on /api/admin/allergens and report isolation between users."""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    with open('/app/frontend/.env') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BASE_URL = line.split('=', 1)[1].strip().rstrip('/')

def _admin_credential(key, default=""):
    """Read admin credentials from env, falling back to backend/.env (no hardcoded secrets)."""
    value = os.environ.get(key)
    if value:
        return value
    try:
        with open('/app/backend/.env') as f:
            for line in f:
                if line.startswith(key + '='):
                    return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return default


ADMIN_EMAIL = _admin_credential("ADMIN_EMAIL")
ADMIN_PASSWORD = _admin_credential("ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def user_session():
    s = requests.Session()
    email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "secret123",
                     "first_name": "Foo", "last_name": "Bar"}, timeout=15)
    assert r.status_code == 200, r.text
    s.email = email  # attach for later
    return s


@pytest.fixture(scope="module")
def user_session_2():
    s = requests.Session()
    email = f"test_user2_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "secret123",
                     "first_name": "Zed", "last_name": "Zap"}, timeout=15)
    assert r.status_code == 200, r.text
    s.email = email
    return s


class TestRBACAdminAllergens:
    def test_user_forbidden_get(self, user_session):
        r = user_session.get(f"{BASE_URL}/api/admin/allergens", timeout=15)
        assert r.status_code == 403

    def test_user_forbidden_post(self, user_session):
        payload = {"code": "zTEST_x", "name": "X", "type": "Alimenti",
                   "siss_code": "0000000.00", "siss_description": "x"}
        r = user_session.post(f"{BASE_URL}/api/admin/allergens", json=payload, timeout=15)
        assert r.status_code == 403

    def test_user_forbidden_put(self, user_session):
        r = user_session.put(f"{BASE_URL}/api/admin/allergens/f1",
                             json={"code": "f1", "name": "n", "type": "Alimenti",
                                   "siss_code": "0090681.00", "siss_description": ""}, timeout=15)
        assert r.status_code == 403

    def test_user_forbidden_delete(self, user_session):
        r = user_session.delete(f"{BASE_URL}/api/admin/allergens/f1", timeout=15)
        assert r.status_code == 403

    def test_unauth_admin_endpoints(self):
        r = requests.get(f"{BASE_URL}/api/admin/allergens", timeout=15)
        assert r.status_code == 401


class TestAdminCRUDAllergens:
    code = f"zTEST_{uuid.uuid4().hex[:6]}"

    def test_admin_list(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/admin/allergens", timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 282

    def test_admin_create(self, admin_session):
        payload = {"code": self.code, "name": "TEST Allergene",
                   "type": "Alimenti", "siss_code": "0090681.99",
                   "siss_description": "TEST desc"}
        r = admin_session.post(f"{BASE_URL}/api/admin/allergens", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["code"] == self.code
        # Verify via GET /api/allergens
        r2 = admin_session.get(f"{BASE_URL}/api/allergens", timeout=20)
        assert any(a["code"] == self.code for a in r2.json())

    def test_admin_create_bad_type(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/allergens",
                               json={"code": "zTEST_bad", "name": "X",
                                     "type": "Fake", "siss_code": "1"}, timeout=15)
        assert r.status_code == 400

    def test_admin_create_duplicate(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/admin/allergens",
                               json={"code": self.code, "name": "dup",
                                     "type": "Alimenti", "siss_code": "1"}, timeout=15)
        assert r.status_code == 400

    def test_admin_update(self, admin_session):
        payload = {"code": self.code, "name": "TEST Updated",
                   "type": "Inalanti", "siss_code": "0090682.99",
                   "siss_description": "updated"}
        r = admin_session.put(f"{BASE_URL}/api/admin/allergens/{self.code}",
                              json=payload, timeout=15)
        assert r.status_code == 200
        assert r.json()["name"] == "TEST Updated"
        assert r.json()["type"] == "Inalanti"

    def test_admin_delete(self, admin_session):
        r = admin_session.delete(f"{BASE_URL}/api/admin/allergens/{self.code}", timeout=15)
        assert r.status_code == 200
        # Verify gone
        r2 = admin_session.get(f"{BASE_URL}/api/allergens", timeout=20)
        assert not any(a["code"] == self.code for a in r2.json())

    def test_admin_delete_404(self, admin_session):
        r = admin_session.delete(f"{BASE_URL}/api/admin/allergens/nonexistent_xyz",
                                 timeout=15)
        assert r.status_code == 404


class TestReportIsolation:
    def test_user_sees_only_own_reports(self, admin_session, user_session, user_session_2):
        # admin creates a report
        payload = {"patient": {"first_name": "TEST_Adm", "last_name": "P", "dob": ""},
                   "doctor_name": "Adm", "allergen_codes": ["f1"], "notes": "", "letterhead": ""}
        ra = admin_session.post(f"{BASE_URL}/api/reports", json=payload, timeout=15)
        assert ra.status_code == 200
        admin_rep_id = ra.json()["report_id"]

        # user1 creates its own
        pu = {"patient": {"first_name": "TEST_U1", "last_name": "P", "dob": ""},
              "doctor_name": "U1", "allergen_codes": ["f2"], "notes": "", "letterhead": ""}
        r1 = user_session.post(f"{BASE_URL}/api/reports", json=pu, timeout=15)
        assert r1.status_code == 200
        u1_rep_id = r1.json()["report_id"]

        # user2 has no reports initially -> should see only their own
        r2list = user_session_2.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert all(x["report_id"] != admin_rep_id for x in r2list)
        assert all(x["report_id"] != u1_rep_id for x in r2list)

        # user1 sees own, not admin's
        r1list = user_session.get(f"{BASE_URL}/api/reports", timeout=15).json()
        assert any(x["report_id"] == u1_rep_id for x in r1list)
        assert all(x["report_id"] != admin_rep_id for x in r1list)

        # user1 cannot GET admin's report
        r_forbidden = user_session.get(f"{BASE_URL}/api/reports/{admin_rep_id}", timeout=15)
        assert r_forbidden.status_code == 404

        # user1 cannot DELETE admin's report
        r_del = user_session.delete(f"{BASE_URL}/api/reports/{admin_rep_id}", timeout=15)
        assert r_del.status_code == 404

        # cleanup
        admin_session.delete(f"{BASE_URL}/api/reports/{admin_rep_id}", timeout=15)
        user_session.delete(f"{BASE_URL}/api/reports/{u1_rep_id}", timeout=15)
