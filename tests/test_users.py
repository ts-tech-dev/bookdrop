def test_create_and_get_user(client):
    response = client.post("/users", json={"email": "reader@example.com"})
    assert response.status_code == 201
    user_id = response.json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "reader@example.com"


def test_get_missing_user_returns_404(client):
    response = client.get("/users/999")
    assert response.status_code == 404
