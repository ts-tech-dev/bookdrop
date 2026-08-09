def test_create_author_and_subscribe(client):
    author_response = client.post("/authors", json={"name": "Brandon Sanderson"})
    assert author_response.status_code == 201
    author_id = author_response.json()["id"]

    user_response = client.post("/users", json={"email": "reader@example.com"})
    user_id = user_response.json()["id"]

    subscribe_response = client.post(f"/authors/{author_id}/subscribe/{user_id}")
    assert subscribe_response.status_code == 201
