"""Audit trail + admin user role management tests."""
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


def _cred(key):
    v = os.environ.get(key)
    if v:
        return v
    try:
        with open('/app/backend/.env') as f:
            for line in f:
                if line.startswith(key + '='):
                    return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return ""


ADMIN_EMAIL = _cred("ADMIN_EMAIL")
ADMIN_PASSWORD = _cred("ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def admin():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200
    me = s.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
    s.user_id = me["user_id"]
    s.email = me["email"]
    return s


@pytest.fixture(scope="module")
def normal_user():
    s = requests.Session()
    email = f"test_ops_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"email": email, "password": "secret123",
                     "first_name": "Op", "last_name": "User"}, timeout=15)
    assert r.status_code == 200
    me = s.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
    s.user_id = me["user_id"]
    s.email = email
    return s


class TestRBACNewEndpoints:
    def test_unauth_audit(self):
        r = requests.get(f"{BASE_URL}/api/admin/audit", timeout=10)
        assert r.status_code == 401

    def test_unauth_users(self):
        r = requests.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert r.status_code == 401

    def test_unauth_role(self):
        r = requests.put(f"{BASE_URL}/api/admin/users/xxx/role",
                         json={"role": "admin"}, timeout=10)
        assert r.status_code == 401

    def test_forbidden_audit(self, normal_user):
        r = normal_user.get(f"{BASE_URL}/api/admin/audit", timeout=10)
        assert r.status_code == 403

    def test_forbidden_users(self, normal_user):
        r = normal_user.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert r.status_code == 403

    def test_forbidden_role(self, normal_user):
        r = normal_user.put(f"{BASE_URL}/api/admin/users/{normal_user.user_id}/role",
                            json={"role": "admin"}, timeout=10)
        assert r.status_code == 403


class TestAuditTrail:
    code = f"zTEST_{uuid.uuid4().hex[:6]}"

    def test_create_logs_audit(self, admin):
        payload = {"code": self.code, "name": "AUD Test",
                   "type": "Alimenti", "siss_code": "0090681.99",
                   "siss_description": "aud desc"}
        r = admin.post(f"{BASE_URL}/api/admin/allergens", json=payload, timeout=15)
        assert r.status_code == 200

        audit = admin.get(f"{BASE_URL}/api/admin/audit", timeout=15).json()
        assert isinstance(audit, list) and len(audit) > 0
        top = audit[0]
        assert top["action"] == "create"
        assert top["allergen_code"] == self.code
        assert top["allergen_name"] == "AUD Test"
        assert top["changed_by_email"] == admin.email
        assert "changed_by_name" in top and top["changed_by_name"]
        assert "timestamp" in top

    def test_update_logs_details(self, admin):
        payload = {"code": self.code, "name": "AUD Test Renamed",
                   "type": "Inalanti", "siss_code": "0090681.99",
                   "siss_description": "aud desc"}
        r = admin.put(f"{BASE_URL}/api/admin/allergens/{self.code}",
                      json=payload, timeout=15)
        assert r.status_code == 200
        audit = admin.get(f"{BASE_URL}/api/admin/audit", timeout=15).json()
        top = audit[0]
        assert top["action"] == "update"
        assert top["allergen_code"] == self.code
        # details should list changed fields (name/type at least)
        det = top.get("details", "")
        assert "name" in det or "type" in det

    def test_delete_logs_audit(self, admin):
        r = admin.delete(f"{BASE_URL}/api/admin/allergens/{self.code}", timeout=15)
        assert r.status_code == 200
        audit = admin.get(f"{BASE_URL}/api/admin/audit", timeout=15).json()
        top = audit[0]
        assert top["action"] == "delete"
        assert top["allergen_code"] == self.code


class TestUserRoleManagement:
    def test_admin_can_list_users(self, admin):
        r = admin.get(f"{BASE_URL}/api/admin/users", timeout=15)
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list) and len(users) > 0
        assert any(u["email"] == admin.email for u in users)
        # ensure no password_hash / _id leak
        assert all("password_hash" not in u and "_id" not in u for u in users)

    def test_self_role_change_400(self, admin):
        r = admin.put(f"{BASE_URL}/api/admin/users/{admin.user_id}/role",
                      json={"role": "user"}, timeout=10)
        assert r.status_code == 400

    def test_invalid_role_400(self, admin, normal_user):
        r = admin.put(f"{BASE_URL}/api/admin/users/{normal_user.user_id}/role",
                      json={"role": "superadmin"}, timeout=10)
        assert r.status_code == 400

    def test_nonexistent_404(self, admin):
        r = admin.put(f"{BASE_URL}/api/admin/users/nonexistent_xyz/role",
                      json={"role": "admin"}, timeout=10)
        assert r.status_code == 404

    def test_promote_then_demote(self, admin, normal_user):
        # Promote
        r = admin.put(f"{BASE_URL}/api/admin/users/{normal_user.user_id}/role",
                      json={"role": "admin"}, timeout=10)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

        # Promoted user should now access admin endpoints
        r2 = normal_user.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert r2.status_code == 200
        r3 = normal_user.get(f"{BASE_URL}/api/admin/audit", timeout=10)
        assert r3.status_code == 200

        # Demote
        r4 = admin.put(f"{BASE_URL}/api/admin/users/{normal_user.user_id}/role",
                       json={"role": "user"}, timeout=10)
        assert r4.status_code == 200
        assert r4.json()["role"] == "user"

        # Now forbidden again
        r5 = normal_user.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert r5.status_code == 403
