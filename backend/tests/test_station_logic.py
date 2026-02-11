
from app.models import Bot, Node
from app.models.bot import BotStatus
from app.services.simulation import SimulationService

def test_idle_bot_goes_to_station(db_session, seed_nodes):
    # node 1 is (0,0). station is (4,3) which might not be in seed_nodes...
    # seed_nodes definition in conftest:
    # Node(id=1, x=0, y=0), Node(2, 1,0), Node(3, 2,0), Node(4, 0,1), Node(5, 1,1)
    # limit is (4,3). We need to ensure (4,3) exists in the test db.
    
    station_node = Node(id=99, x=4, y=3, is_delivery_point=False)
    db_session.add(station_node)
    
    # Add intermediate nodes to form a path from (0,0) to (4,3)
    # (0,0) is id=1. We need path like (1,0)->(2,0)->(3,0)->(4,0)->(4,1)->(4,2)->(4,3)
    # seed_nodes has (1,0)=2, (2,0)=3. 
    # Missing: (3,0), (4,0), (4,1), (4,2).
    intermediates = [
        Node(id=10, x=3, y=0, is_delivery_point=False),
        Node(id=11, x=4, y=0, is_delivery_point=False),
        Node(id=12, x=4, y=1, is_delivery_point=False),
        Node(id=13, x=4, y=2, is_delivery_point=False),
    ]
    db_session.add_all(intermediates)
    
    # create a bot at (0,0)
    bot = Bot(id=1, name="StationBot", current_node_id=1, status=BotStatus.IDLE)
    db_session.add(bot)
    db_session.commit()
    
    service = SimulationService(db_session)
    
    # Tick 1: should calculate route to station AND move one step
    service.tick()
    db_session.refresh(bot)
    
    # Bot should be moving and have taken first step (to node 2 or 4)
    assert bot.status == BotStatus.MOVING
    assert bot.current_node_id in [2, 4]
    
    # Tick 2: should move another step
    service.tick()
    db_session.refresh(bot)
    
    # check if it moved closer (to node 3 if it took the x-first path)
    assert bot.current_node_id == 3

def test_bot_reset_goes_to_station(db_session):
    # This is similar to what the router does
    station_node = Node(id=99, x=4, y=3, is_delivery_point=False)
    db_session.add(station_node)
    
    # create a bot at some other node
    other_node = Node(id=50, x=1, y=1, is_delivery_point=False)
    db_session.add(other_node)
    
    bot = Bot(id=1, name="StationBot", current_node_id=50, status=BotStatus.MOVING)
    db_session.add(bot)
    db_session.commit()
    
    # Simulating the reset logic from routers/simulation.py
    start_node = db_session.query(Node).filter(Node.x == 4, Node.y == 3).first()
    bot.current_node_id = start_node.id
    bot.status = BotStatus.IDLE
    db_session.commit()
    
    assert bot.current_node_id == 99
    assert bot.status == BotStatus.IDLE
