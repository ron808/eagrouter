# order api tests - create, get, cancel

def test_create_order(client, seed_all):
    # order from ramen restaurant to delivery node 2
    response = client.post("/api/orders", json={
        "restaurant_id": 1,
        "delivery_node_id": 2,
    })
    assert response.status_code == 201
    order = response.json()
    assert order["restaurant_name"] == "RAMEN"
    assert order["delivery_node_id"] == 2
    # should get auto-assigned to a bot since we have idle ones
    assert order["status"] in ["PENDING", "ASSIGNED"]


def test_create_order_invalid_restaurant(client, seed_all):
    # restaurant 999 doesn't exist, should blow up
    response = client.post("/api/orders", json={
        "restaurant_id": 999,
        "delivery_node_id": 2,
    })
    assert response.status_code == 404


def test_create_order_invalid_delivery_node(client, seed_all):
    # node 1 is not a delivery point
    response = client.post("/api/orders", json={
        "restaurant_id": 1,
        "delivery_node_id": 1,
    })
    assert response.status_code == 400


def test_restaurant_throttle(client, seed_all):
    # first 3 orders should succeed (the limit)
    for i in range(3):
        resp = client.post("/api/orders", json={
            "restaurant_id": 1,
            "delivery_node_id": 2,
        })
        assert resp.status_code == 201, f"Order {i+1} should succeed"

    # 4th order within 30s window should be rejected with 429
    resp = client.post("/api/orders", json={
        "restaurant_id": 1,
        "delivery_node_id": 2,
    })
    assert resp.status_code == 429
    assert "RAMEN" in resp.json()["detail"]
    assert "Max 3 allowed" in resp.json()["detail"]


def test_cancel_order(client, seed_all):
    # create then cancel
    create_resp = client.post("/api/orders", json={
        "restaurant_id": 1,
        "delivery_node_id": 2,
    })
    order_id = create_resp.json()["id"]

    cancel_resp = client.delete(f"/api/orders/{order_id}")
    assert cancel_resp.status_code == 204
