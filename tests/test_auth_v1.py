# all tests in this file are ai generated

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app  # adjust to your app's entry point

client = TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# Session-scoped fixtures — created once, reused across all tests
# These avoid UniqueViolation errors from repeated inserts of the same data.
# ===========================================================================


@pytest.fixture(scope="session")
def owner_cookies():
    """Register alice_owner once and return her login cookies."""
    client.post(
        "/auth/v1/create-shop-owner",
        json={
            "name": "Alice",
            "username": "alice_owner",
            "pin": "1234",
        },
    )
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "owner",
        },
    )
    assert r.status_code == 200, f"Owner login failed: {r.json()}"
    return r.cookies


@pytest.fixture(scope="session")
def shop_id(owner_cookies):
    """Create a shop once and return its id."""
    r = client.post(
        "/shop/v1/create-shop",
        json={
            "name": "Test Shop",
            "location": "Nairobi",
        },
        cookies=owner_cookies,
    )
    assert r.status_code == 200, f"Shop creation failed: {r.json()}"
    return r.json()["shop_id"]  # requires create-shop to return shop_id in response


@pytest.fixture(scope="session")
def employee_cookies(owner_cookies, shop_id):
    """Create bob_emp once and return his login cookies."""
    client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Bob",
            "username": "bob_emp",
            "pin": "5678",
        },
        cookies=owner_cookies,
    )
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "bob_emp",
            "pin": "5678",
            "category": "employee",
        },
    )
    assert r.status_code == 200, f"Employee login failed: {r.json()}"
    return r.cookies


# ===========================================================================
# POST /auth/v1/create-shop-owner
# ===========================================================================


def test_create_shop_owner_success():
    r = client.post(
        "/auth/v1/create-shop-owner",
        json={
            "name": "Owner Two",
            "username": "owner_two",
            "pin": "4321",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"detail": "Register successful."}


def test_create_shop_owner_missing_name():
    r = client.post(
        "/auth/v1/create-shop-owner",
        json={
            "username": "owner_x",
            "pin": "1234",
        },
    )
    assert r.status_code == 422


def test_create_shop_owner_missing_username():
    r = client.post(
        "/auth/v1/create-shop-owner",
        json={
            "name": "Owner X",
            "pin": "1234",
        },
    )
    assert r.status_code == 422


def test_create_shop_owner_missing_pin():
    r = client.post(
        "/auth/v1/create-shop-owner",
        json={
            "name": "Owner X",
            "username": "owner_x",
        },
    )
    assert r.status_code == 422


def test_create_shop_owner_empty_body():
    r = client.post("/auth/v1/create-shop-owner", json={})
    assert r.status_code == 422


# ===========================================================================
# POST /auth/v1/login
# ===========================================================================


def test_login_owner_success(owner_cookies):
    # fixture already verified this, but test it explicitly too
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "owner",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"detail": "Login successful."}


def test_login_employee_success(employee_cookies):
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "bob_emp",
            "pin": "5678",
            "category": "employee",
        },
    )
    assert r.status_code == 200
    assert r.json() == {"detail": "Login successful."}


def test_login_wrong_pin():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "0000",
            "category": "owner",
        },
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "The sign in details are incorrect."}


def test_login_wrong_username():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "nobody",
            "pin": "1234",
            "category": "owner",
        },
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "The sign in details are incorrect."}


def test_login_invalid_category():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "admin",
        },
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid category"}


def test_login_owner_using_employee_category():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "employee",
        },
    )
    assert r.status_code == 401


def test_login_employee_using_owner_category(employee_cookies):
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "bob_emp",
            "pin": "5678",
            "category": "owner",
        },
    )
    assert r.status_code == 401


def test_login_missing_pin():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "category": "owner",
        },
    )
    assert r.status_code == 422


def test_login_empty_body():
    r = client.post("/auth/v1/login", json={})
    assert r.status_code == 422


def test_login_sets_cookies():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "owner",
        },
    )
    assert r.status_code == 200
    assert len(r.cookies) > 0


# ===========================================================================
# POST /auth/v1/create-employee
# ===========================================================================


def test_create_employee_not_authenticated(shop_id):
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Ghost",
            "username": "ghost_emp",
            "pin": "0000",
        },
    )
    assert r.status_code in (400, 401, 403)


def test_create_employee_success(owner_cookies, shop_id):
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Carol",
            "username": "carol_emp",
            "pin": "1111",
        },
        cookies=owner_cookies,
    )
    assert r.status_code == 200
    assert r.json() == {"detail": "Employee create successful."}


def test_create_employee_duplicate_username(owner_cookies, shop_id):
    # bob_emp already exists from the session fixture
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Bob Duplicate",
            "username": "bob_emp",
            "pin": "9999",
        },
        cookies=owner_cookies,
    )
    assert r.status_code == 409
    assert r.json() == {"detail": "Employee already exists."}


def test_create_employee_as_employee_is_rejected(employee_cookies, shop_id):
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Charlie",
            "username": "charlie_emp",
            "pin": "2222",
        },
        cookies=employee_cookies,
    )
    assert r.status_code == 400
    assert r.json() == {"detail": "Failed to create employee."}


def test_create_employee_missing_fields(owner_cookies):
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "name": "Incomplete",
        },
        cookies=owner_cookies,
    )
    assert r.status_code == 422


# ===========================================================================
# POST /auth/v1/logout
# ===========================================================================


def test_logout_success():
    r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "owner",
        },
    )
    logout = client.post("/auth/v1/logout", cookies=r.cookies)
    assert logout.status_code == 200
    assert logout.json() == {"detail": "Successfully logged out"}


def test_logout_not_authenticated():
    r = client.post("/auth/v1/logout")
    assert r.status_code in (401, 403)


def test_logout_invalidates_session(shop_id):
    login_r = client.post(
        "/auth/v1/login",
        json={
            "username": "alice_owner",
            "pin": "1234",
            "category": "owner",
        },
    )
    stale_cookies = login_r.cookies

    logout_r = client.post("/auth/v1/logout", cookies=stale_cookies)
    assert logout_r.status_code == 200

    # using the pre-logout cookies should no longer grant access
    r = client.post(
        "/auth/v1/create-employee",
        json={
            "shop_id": shop_id,
            "name": "Test",
            "username": "test_emp_stale",
            "pin": "0000",
        },
        cookies=stale_cookies,
    )
    assert r.status_code in (400, 401, 403)
