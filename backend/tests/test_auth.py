import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import DB_PATH
from app.api.auth import sessions

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    #clean db before each test
    if DB_PATH.exists():
        DB_PATH.unlink()
    sessions.clear()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()
    sessions.clear()

def test_unlock_valid_seed():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    response = client.post("/api/auth/unlock", json={"seed_phrase": seed})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "session_token" in response.cookies

def test_unlock_invalid_seed():
    response = client.post("/api/auth/unlock", json={"seed_phrase": "invalid seed"})
    assert response.status_code == 400
    assert "Invalid seed phrase" in response.json()["detail"]

def test_status_unlocked():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    unlock_response = client.post("/api/auth/unlock", json={"seed_phrase": seed})
    cookies = {"session_token": unlock_response.cookies.get("session_token")}
    status_response = client.get("/api/auth/status", cookies=cookies)
    assert status_response.status_code == 200
    assert status_response.json()["unlocked"] is True

def test_status_locked():
    response = client.get("/api/auth/status")
    assert response.status_code == 200
    assert response.json()["unlocked"] is False

def test_lock():
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    unlock_response = client.post("/api/auth/unlock", json={"seed_phrase": seed})
    cookies = {"session_token": unlock_response.cookies.get("session_token")}
    lock_response = client.post("/api/auth/lock", cookies=cookies)
    assert lock_response.status_code == 200
    assert lock_response.json()["status"] == "success"
    #verify now locked
    status_response = client.get("/api/auth/status", cookies=cookies)
    assert status_response.json()["unlocked"] is False

def test_seed_not_persisted():
    #I4 compliance: seed phrase never stored
    seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    client.post("/api/auth/unlock", json={"seed_phrase": seed})
    #read db file as binary, check seed not in it
    if DB_PATH.exists():
        content = DB_PATH.read_bytes()
        assert b"abandon" not in content
