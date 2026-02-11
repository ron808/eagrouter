# grid api tests - nodes, restaurants, delivery points

def test_get_nodes(client, seed_nodes):
    response = client.get("/api/grid/nodes")
    assert response.status_code == 200
    nodes = response.json()
    assert len(nodes) == 5
    # make sure the address format is in there
    assert "address" in nodes[0]


def test_get_grid_full(client, seed_nodes, seed_restaurant):
    # the big combined endpoint the frontend uses
    response = client.get("/api/grid")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 5
    assert len(data["restaurants"]) == 1
    assert data["restaurants"][0]["name"] == "RAMEN"
    # should have 2 delivery points based on our seed data
    assert len(data["delivery_points"]) == 2


def test_get_node_not_found(client, seed_nodes):
    response = client.get("/api/grid/nodes/999")
    assert response.status_code == 404
