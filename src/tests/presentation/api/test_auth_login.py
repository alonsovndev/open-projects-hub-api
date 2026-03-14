from fastapi.testclient import TestClient


def test_login_success_returns_frontend_shape(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "alonsonh94@gmail.com", "password": "demo123!A"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["token"] == "mock-token-user-1"
    assert body["email"] == "alonsonh94@gmail.com"
    assert body["displayName"] == "Alonso"
    assert body["loggedInAt"].endswith("Z")


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "alonsonh94@gmail.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_allows_local_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
