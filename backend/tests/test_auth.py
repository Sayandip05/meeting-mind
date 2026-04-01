import pytest


def test_signup_success(client):
    """Test successful user registration"""
    user_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User"
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == user_data["email"]
    assert data["user"]["full_name"] == user_data["full_name"]


def test_signup_duplicate_email(client, test_user):
    """Test registration with duplicate email"""
    user_data = {
        "email": "test@example.com",  # Same as test_user fixture
        "password": "password123",
        "full_name": "Another User"
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test successful login"""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == login_data["email"]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user(client, test_user):
    """Test getting current user info"""
    token = test_user["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
