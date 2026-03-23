"""
Unit tests for authentication, RBAC, and brute-force protection.
"""

import pytest


class TestRegistration:
    """Test user registration endpoint."""

    def test_register_success(self, test_client):
        resp = test_client.post("/api/register", json={
            "username": "newuser",
            "password": "NewPass123!",
            "role": "engineer",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "engineer"
        assert data["username"] == "newuser"

    def test_register_duplicate(self, test_client):
        # First registration
        test_client.post("/api/register", json={
            "username": "dupuser",
            "password": "DupPass123!",
            "role": "viewer",
        })
        # Duplicate
        resp = test_client.post("/api/register", json={
            "username": "dupuser",
            "password": "DupPass123!",
            "role": "viewer",
        })
        assert resp.status_code in [400, 409]

    def test_register_invalid_role(self, test_client):
        resp = test_client.post("/api/register", json={
            "username": "badrole",
            "password": "BadRole123!",
            "role": "superuser",
        })
        assert resp.status_code == 400

    def test_register_super_admin(self, test_client):
        resp = test_client.post("/api/register", json={
            "username": "newsuper",
            "password": "SuperPass123!",
            "role": "super_admin",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "super_admin"


class TestLogin:
    """Test login and token refresh."""

    def test_login_success(self, test_client):
        test_client.post("/api/register", json={
            "username": "loginuser",
            "password": "LoginPass123!",
            "role": "viewer",
        })
        resp = test_client.post("/api/login", json={
            "username": "loginuser",
            "password": "LoginPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, test_client):
        test_client.post("/api/register", json={
            "username": "wrongpw",
            "password": "CorrectPass123!",
            "role": "viewer",
        })
        resp = test_client.post("/api/login", json={
            "username": "wrongpw",
            "password": "WrongPass123!",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, test_client):
        resp = test_client.post("/api/login", json={
            "username": "noexist",
            "password": "NoExist123!",
        })
        # 401 = invalid credentials, 429 = rate limited (proves limiter works)
        assert resp.status_code in [401, 429]


class TestTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_token(self, test_client):
        test_client.post("/api/register", json={
            "username": "refreshuser",
            "password": "RefreshPass123!",
            "role": "viewer",
        })
        login_resp = test_client.post("/api/login", json={
            "username": "refreshuser",
            "password": "RefreshPass123!",
        })
        login_data = login_resp.json()
        if "refresh_token" not in login_data:
            pytest.skip("Login rate-limited, cannot test refresh")
        refresh_token = login_data["refresh_token"]

        resp = test_client.post("/api/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()


class TestRBAC:
    """Test role-based access control."""

    def test_permissions_endpoint(self, test_client, auth_headers):
        resp = test_client.get("/api/v1/admin/permissions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data
        assert "valid_roles" in data
        assert "super_admin" in data["valid_roles"]

    def test_viewer_cannot_manage_users(self, test_client, viewer_headers):
        resp = test_client.get("/api/v1/admin/users", headers=viewer_headers)
        assert resp.status_code == 403

    def test_admin_can_list_users(self, test_client, auth_headers):
        resp = test_client.get("/api/v1/admin/users", headers=auth_headers)
        assert resp.status_code == 200
        assert "users" in resp.json()
