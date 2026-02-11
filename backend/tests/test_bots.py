# bot api tests

def test_get_bots(client, seed_bots):
    response = client.get("/api/bots")
    assert response.status_code == 200
    bots = response.json()
    assert len(bots) == 2
    # both should be idle with no active orders
    for bot in bots:
        assert bot["status"] == "IDLE"
        assert bot["current_order_count"] == 0


def test_get_single_bot(client, seed_bots):
    response = client.get("/api/bots/1")
    assert response.status_code == 200
    bot = response.json()
    assert bot["name"] == "Bot-1"
    assert bot["available_capacity"] == 3


def test_get_bot_not_found(client, seed_bots):
    response = client.get("/api/bots/999")
    assert response.status_code == 404
