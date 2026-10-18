def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon_is_served_and_linked(client):
    res = client.get("/favicon.svg")

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert res.text.startswith("<svg")
    assert '<link rel="icon" type="image/svg+xml" href="/favicon.svg">' in client.get("/").text
