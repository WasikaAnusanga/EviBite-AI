from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_auth_signup_and_signin():
    email = f"test_user_{id(app)}@example.com"
    password = "secretpassword123"

    # 1. Test signup without food allergies field
    signup_payload = {
        "full_name": "Test User",
        "email": email,
        "password": password,
    }
    resp = client.post("/api/auth/signup", json=signup_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

    token = data["access_token"]

    # 2. Test get /api/auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 3. Test signin with correct password
    signin_resp = client.post("/api/auth/signin", json={"email": email, "password": password})
    assert signin_resp.status_code == 200
    assert "access_token" in signin_resp.json()

    # 4. Test signin with wrong password
    bad_signin = client.post("/api/auth/signin", json={"email": email, "password": "wrongpassword"})
    assert bad_signin.status_code == 401


def test_unauthenticated_chat_rejected():
    # Calling /api/chat without Authorization header should return 401
    resp = client.post("/api/chat", json={"message": "Is Nutella safe?"})
    assert resp.status_code == 401


def test_authenticated_chat_and_history():
    email = f"chat_user_{id(app)}@example.com"
    password = "password123"

    # Signup
    signup_resp = client.post("/api/auth/signup", json={"full_name": "Chat Test User", "email": email, "password": password})
    token = signup_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Send chat message
    chat_payload = {"message": "Are almonds safe for peanut allergy?"}
    chat_resp = client.post("/api/chat", json=chat_payload, headers=headers)
    assert chat_resp.status_code == 200, chat_resp.text
    chat_data = chat_resp.json()
    assert "final_response" in chat_data
    session_id = chat_data["session_id"]
    assert session_id is not None

    # Fetch user chat sessions
    history_resp = client.get("/api/history", headers=headers)
    assert history_resp.status_code == 200
    sessions = history_resp.json()["sessions"]
    assert len(sessions) >= 1
    found = any(s["session_id"] == session_id for s in sessions)
    assert found

    # Fetch session messages
    msg_resp = client.get(f"/api/history/{session_id}", headers=headers)
    assert msg_resp.status_code == 200
    messages = msg_resp.json()["messages"]
    assert len(messages) >= 2  # user message + assistant response
