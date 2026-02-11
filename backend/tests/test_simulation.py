# simulation api tests - start, stop, status

def test_simulation_status(client, seed_all):
    response = client.get("/api/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["is_running"] == False
    assert data["tick_count"] == 0


def test_start_stop_simulation(client, seed_all):
    # start it
    start = client.post("/api/simulation/start")
    assert start.status_code == 200
    assert start.json()["is_running"] == True

    # stop it
    stop = client.post("/api/simulation/stop")
    assert stop.status_code == 200
    assert stop.json()["is_running"] == False
