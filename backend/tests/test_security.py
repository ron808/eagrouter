# security middleware tests - headers, rate limiting

def test_security_headers_present(client):
    # every response should have these headers
    response = client.get("/")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "strict-origin" in response.headers.get("Referrer-Policy", "")


def test_request_goes_through_normally(client, seed_nodes):
    # just making sure the middleware doesn't break normal requests
    response = client.get("/api/grid/nodes")
    assert response.status_code == 200
    assert len(response.json()) == 5
