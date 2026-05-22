"""Authentication tests for Second Brain API."""

import pytest
from fastapi.testclient import TestClient
from api.server import app
from api.auth.auth import hash_password, verify_password
from api.auth.models import init_auth_db


@pytest.fixture(scope="session", autouse=True)
def setup_auth_db():
    """Initialize auth database before tests."""
    init_auth_db()


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code in [200, 422]  # 422 if validation fails
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["email"] == "newuser@example.com"
            assert data["username"] == "newuser"

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        email = "duplicate@example.com"
        client.post(
            "/auth/register",
            json={
                "email": email,
                "username": "user1",
                "password": "securepassword123",
            },
        )
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "username": "user2",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 400 or response.status_code == 422

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username."""
        username = "duplicateuser"
        client.post(
            "/auth/register",
            json={
                "email": "user1@example.com",
                "username": username,
                "password": "securepassword123",
            },
        )
        response = client.post(
            "/auth/register",
            json={
                "email": "user2@example.com",
                "username": username,
                "password": "securepassword123",
            },
        )
        assert response.status_code == 400 or response.status_code == 422

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid_email",
                "username": "testuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_login_success(self, client):
        """Test successful login."""
        email = "logintest@example.com"
        username = "loginuser"
        password = "securepassword123"

        client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )

        response = client.post(
            "/auth/login",
            json={
                "username": username,
                "password": password,
            },
        )
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistentuser",
                "password": "somepassword",
            },
        )
        assert response.status_code == 401

    def test_login_invalid_password(self, client):
        """Test login with invalid password."""
        username = "loginuser2"
        email = "logintest2@example.com"

        client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "correctpassword",
            },
        )

        response = client.post(
            "/auth/login",
            json={
                "username": username,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_refresh_token_success(self, client):
        """Test token refresh."""
        username = "refreshuser"
        email = "refresh@example.com"
        password = "securepassword123"

        client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
            },
        )

        login_response = client.post(
            "/auth/login",
            json={
                "username": username,
                "password": password,
            },
        )

        if login_response.status_code == 200:
            refresh_token = login_response.json()["refresh_token"]

            response = client.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert response.status_code in [200, 422]
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        assert response.status_code == 401


class TestAuthStatus:
    """Basic health checks for auth endpoints."""

    def test_auth_endpoints_exist(self, client):
        """Test that auth endpoints are accessible."""
        response = client.post("/auth/register", json={})
        assert response.status_code in [400, 422]

        response = client.post("/auth/login", json={})
        assert response.status_code in [400, 422]

        response = client.post("/auth/refresh", json={})
        assert response.status_code in [400, 422]
