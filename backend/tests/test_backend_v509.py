"""Backend regression tests for GestaoEPI v5.0.9 with the 5 critical improvements.

Covered:
  * Auth (/api/auth/login)
  * Employees CRUD + biometric consent (accept/refuse persistence)
  * Biometric check-duplicate
  * Deliveries with quantity + size persistence
  * PDF Report generation
  * General health of EPIs / Companies / Kits / Dashboard
"""
import os
import json
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_USERNAME = os.environ.get("TEST_ADMIN_USERNAME", "administrador")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "")


# ---------- helpers / fixtures ----------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data, f"no access_token in {data}"
    # must_change_password expected to be True for first login but token must be valid
    assert data.get("must_change_password") in (True, False)
    return data["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def company_id(auth_headers):
    r = requests.get(f"{API}/companies", headers=auth_headers, timeout=20)
    assert r.status_code == 200, f"companies GET failed: {r.text}"
    companies = r.json()
    assert isinstance(companies, list) and len(companies) > 0, "no companies seeded"
    return companies[0]["id"]


@pytest.fixture(scope="session")
def seed_employee_id(auth_headers):
    r = requests.get(f"{API}/employees", headers=auth_headers, timeout=20)
    assert r.status_code == 200
    emps = r.json()
    # try João da Silva
    target = next((e for e in emps if "joão" in e.get("full_name", "").lower() or "joao" in e.get("full_name", "").lower()), None)
    if target is None and emps:
        target = emps[0]
    assert target is not None, "no employee seeded"
    return target["id"]


# ---------- 1. Auth ----------

class TestAuth:
    def test_login_admin(self):
        r = requests.post(f"{API}/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 10
        # must_change_password expected True on first login
        assert "must_change_password" in data

    def test_login_invalid_password(self):
        r = requests.post(f"{API}/auth/login", json={"username": ADMIN_USERNAME, "password": "wrong"}, timeout=20)
        assert r.status_code in (400, 401, 422), r.text


# ---------- 2. Employees CRUD + facial_consent ----------

class TestEmployees:
    def test_list_employees(self, auth_headers):
        r = requests.get(f"{API}/employees", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        emps = r.json()
        assert isinstance(emps, list)
        # João da Silva from seed
        names = [e.get("full_name", "").lower() for e in emps]
        assert any("jo" in n and "silva" in n for n in names), f"João da Silva not seeded. names={names[:5]}"

    def _create_employee(self, headers, company_id, facial_consent: bool):
        suffix = uuid.uuid4().hex[:8]
        # Generate fake CPF-like (just digits)
        cpf = f"{uuid.uuid4().int % 10**11:011d}"
        payload = {
            "full_name": f"TEST_Func_{suffix}",
            "cpf": cpf,
            "registration_number": f"TST{suffix}",
            "company_id": company_id,
            "facial_consent": facial_consent,
        }
        r = requests.post(f"{API}/employees", headers=headers, json=payload, timeout=20)
        return r, payload

    def test_create_employee_consent_true(self, auth_headers, company_id):
        r, payload = self._create_employee(auth_headers, company_id, True)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data.get("facial_consent") is True
        assert data.get("full_name") == payload["full_name"]
        # cleanup
        requests.delete(f"{API}/employees/{data['id']}", headers=auth_headers, timeout=20)

    def test_create_employee_consent_false(self, auth_headers, company_id):
        r, payload = self._create_employee(auth_headers, company_id, False)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data.get("facial_consent") is False
        # GET to verify persistence
        eid = data["id"]
        g = requests.get(f"{API}/employees/{eid}", headers=auth_headers, timeout=20)
        assert g.status_code == 200
        assert g.json().get("facial_consent") is False
        requests.delete(f"{API}/employees/{eid}", headers=auth_headers, timeout=20)


# ---------- 3. Biometric consent ----------

class TestBiometricConsent:
    @pytest.fixture()
    def temp_employee(self, auth_headers, company_id):
        suffix = uuid.uuid4().hex[:8]
        cpf = f"{uuid.uuid4().int % 10**11:011d}"
        payload = {
            "full_name": f"TEST_Consent_{suffix}",
            "cpf": cpf,
            "registration_number": f"CST{suffix}",
            "company_id": company_id,
            "facial_consent": False,
        }
        r = requests.post(f"{API}/employees", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code in (200, 201), r.text
        eid = r.json()["id"]
        yield eid
        requests.delete(f"{API}/employees/{eid}", headers=auth_headers, timeout=20)

    def test_consent_refuse_persists(self, auth_headers, temp_employee):
        r = requests.post(
            f"{API}/employees/{temp_employee}/biometric-consent",
            headers=auth_headers,
            json={"accepted": False},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("success") is True
        assert "consent_date" in body
        # GET employee verifies persistence of facial_consent=False + facial_consent_date present
        g = requests.get(f"{API}/employees/{temp_employee}", headers=auth_headers, timeout=20)
        assert g.status_code == 200
        emp = g.json()
        assert emp.get("facial_consent") is False
        assert emp.get("facial_consent_date") is not None, "facial_consent_date must be persisted"

    def test_consent_accept_persists(self, auth_headers, temp_employee):
        r = requests.post(
            f"{API}/employees/{temp_employee}/biometric-consent",
            headers=auth_headers,
            json={"accepted": True},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        g = requests.get(f"{API}/employees/{temp_employee}", headers=auth_headers, timeout=20)
        assert g.status_code == 200
        emp = g.json()
        assert emp.get("facial_consent") is True
        assert emp.get("facial_consent_date") is not None

    def test_get_biometric_consent_status(self, auth_headers, temp_employee):
        # accept first
        requests.post(
            f"{API}/employees/{temp_employee}/biometric-consent",
            headers=auth_headers,
            json={"accepted": True},
            timeout=20,
        )
        r = requests.get(f"{API}/employees/{temp_employee}/biometric-consent", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "has_consent" in body
        assert body["has_consent"] is True
        assert "consent_date" in body
        assert "consent_ip" in body


# ---------- 4. Biometric check-duplicate ----------

class TestBiometricDuplicate:
    def test_check_duplicate_zero_vector(self, auth_headers):
        descriptor = json.dumps([0.0] * 128)
        r = requests.post(
            f"{API}/biometric/check-duplicate",
            headers=auth_headers,
            json={"descriptor": descriptor},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "is_duplicate" in body
        assert "message" in body

    def test_check_duplicate_invalid_descriptor(self, auth_headers):
        r = requests.post(
            f"{API}/biometric/check-duplicate",
            headers=auth_headers,
            json={"descriptor": json.dumps([0.0] * 64)},  # wrong size
            timeout=20,
        )
        assert r.status_code == 400, r.text


# ---------- 5. Deliveries with quantity + size ----------

class TestDeliveries:
    @pytest.fixture(scope="class")
    def epi_id_for_delivery(self, auth_headers):
        # Try to use existing one with size, otherwise create
        r = requests.get(f"{API}/epis", headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        epis = r.json()
        with_size = [e for e in epis if e.get("size") and e.get("current_stock", 0) > 5]
        if with_size:
            return with_size[0]["id"]
        # Create new one
        payload = {
            "name": f"TEST_EPI_{uuid.uuid4().hex[:6]}",
            "type_category": "luva",
            "size": "M",
            "ca_number": f"CA{uuid.uuid4().int % 100000}",
            "current_stock": 100,
        }
        c = requests.post(f"{API}/epis", headers=auth_headers, json=payload, timeout=20)
        assert c.status_code in (200, 201), c.text
        return c.json()["id"]

    @pytest.fixture(scope="class")
    def employee_with_photo(self, auth_headers, company_id):
        # create employee + upload tiny dummy photo so delivery passes the photo gate
        suffix = uuid.uuid4().hex[:8]
        cpf = f"{uuid.uuid4().int % 10**11:011d}"
        payload = {
            "full_name": f"TEST_DelEmp_{suffix}",
            "cpf": cpf,
            "registration_number": f"DEL{suffix}",
            "company_id": company_id,
            "facial_consent": True,
        }
        r = requests.post(f"{API}/employees", headers=auth_headers, json=payload, timeout=20)
        assert r.status_code in (200, 201), r.text
        eid = r.json()["id"]
        # 1x1 PNG bytes
        png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
               b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05"
               b"\xfe\x02\xfe\xa3\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")
        files = {"file": ("photo.png", png, "image/png")}
        h = {"Authorization": auth_headers["Authorization"]}
        up = requests.post(f"{API}/employees/{eid}/photo", headers=h, files=files, timeout=20)
        assert up.status_code == 200, f"upload photo failed: {up.text}"
        yield eid
        requests.delete(f"{API}/employees/{eid}", headers=auth_headers, timeout=20)

    def test_create_delivery_with_size_and_quantity(self, auth_headers, employee_with_photo, epi_id_for_delivery):
        payload = {
            "employee_id": employee_with_photo,
            "delivery_type": "individual",
            "is_return": False,
            "items": [
                {"epi_id": epi_id_for_delivery, "quantity": 3, "size": "M"}
            ],
        }
        r = requests.post(f"{API}/deliveries", headers=auth_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert item.get("quantity") == 3, f"quantity not persisted: {item}"
        assert item.get("size") == "M", f"size not persisted: {item}"

        # GET deliveries and verify
        g = requests.get(f"{API}/deliveries", headers=auth_headers, timeout=20)
        assert g.status_code == 200
        deliveries = g.json()
        assert any(
            any(it.get("size") == "M" and it.get("quantity") == 3 for it in d.get("items", []))
            for d in deliveries
        ), "no delivery with size=M qty=3 found in GET"


# ---------- 6. PDF Report ----------

class TestReports:
    def test_employee_pdf(self, auth_headers, seed_employee_id):
        r = requests.get(
            f"{API}/reports/employee/{seed_employee_id}/pdf",
            headers={"Authorization": auth_headers["Authorization"]},
            timeout=30,
        )
        assert r.status_code == 200, r.text[:500]
        ct = r.headers.get("content-type", "")
        assert "pdf" in ct.lower(), f"expected pdf content-type, got {ct}"
        assert r.headers.get("content-disposition"), "missing Content-Disposition"
        assert len(r.content) > 100, f"pdf too small: {len(r.content)} bytes"


# ---------- 7. Other critical routes (smoke) ----------

class TestSmokeRoutes:
    @pytest.mark.parametrize("path", ["/epis", "/companies", "/kits", "/employees"])
    def test_list_smoke(self, auth_headers, path):
        r = requests.get(f"{API}{path}", headers=auth_headers, timeout=20)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"
        assert isinstance(r.json(), list)

    def test_dashboard_stats(self, auth_headers):
        r = requests.get(f"{API}/dashboard/stats", headers=auth_headers, timeout=20)
        # Optional endpoint: accept 200 or 404
        assert r.status_code in (200, 404), f"unexpected: {r.status_code} {r.text[:200]}"
