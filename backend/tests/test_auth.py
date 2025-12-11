import pytest
from app.database import Store
from app.routers.auth import get_password_hash

def test_signup(client):
    response = client.post("/auth/signup", json={
        "phone": "+918888888888",
        "store_name": "New Store",
        "password": "StrongPassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+918888888888"
    assert "id" in data

def test_login_success(client):
    # User created by fixture logic if reused, but here we need specific user
    client.post("/auth/signup", json={
        "phone": "+917777777777",
        "store_name": "Login Store",
        "password": "Password123"
    })
    
    response = client.post("/auth/login", json={
        "phone": "+917777777777",
        "password": "Password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure(client):
    response = client.post("/auth/login", json={
        "phone": "+917777777777",
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_rate_limit(client):
    # Create user
    client.post("/auth/signup", json={
        "phone": "+916666666666",
        "store_name": "Rate Limit Store",
        "password": "Password123"
    })
    
    # Fail 5 times
    for _ in range(5):
        client.post("/auth/login", json={
            "phone": "+916666666666",
            "password": "WrongPassword"
        })
    
    # 6th attempt should be blocked
    response = client.post("/auth/login", json={
        "phone": "+916666666666",
        "password": "Password123" # Even correct password should fail now
    })
    assert response.status_code == 429

def test_change_password(client, auth_token):
    # Depends on auth_token user (+919999999999 / Password123)
    
    response = client.post(
        "/auth/change-password",
        json={"old_password": "Password123", "new_password": "NewPassword123"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    
    # Login with new password
    new_login = client.post("/auth/login", json={
        "phone": "+919999999999",
        "password": "NewPassword123"
    })
    assert new_login.status_code == 200
