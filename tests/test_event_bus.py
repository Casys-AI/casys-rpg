import pytest
import pytest_asyncio
from event_bus import EventBus, Event

@pytest_asyncio.fixture(scope="function")
async def event_bus():
    return EventBus()

@pytest.mark.asyncio
async def test_subscribe_and_emit(event_bus):
    """Test l'abonnement et l'émission d'événements"""
    received_data = []
    
    async def listener(event):
        received_data.append(event.data)
    
    await event_bus.subscribe("test_event", listener)
    await event_bus.emit(Event(type="test_event", data={"message": "test"}))
    
    assert len(received_data) == 1
    assert received_data[0]["message"] == "test"

@pytest.mark.asyncio
async def test_multiple_listeners(event_bus):
    """Test plusieurs listeners pour le même événement"""
    count1 = []
    count2 = []
    
    async def listener1(event):
        count1.append(event.data)
    
    async def listener2(event):
        count2.append(event.data)
    
    await event_bus.subscribe("test_event", listener1)
    await event_bus.subscribe("test_event", listener2)
    
    await event_bus.emit(Event(type="test_event", data="data"))
    
    assert len(count1) == len(count2) == 1

@pytest.mark.asyncio
async def test_event_history(event_bus):
    """Test l'historique des événements"""
    await event_bus.emit(Event(type="event1", data="data1"))
    await event_bus.emit(Event(type="event2", data="data2"))
    
    history = event_bus.history
    assert len(history) == 2
    assert history[0].type == "event1"
    assert history[1].type == "event2"

@pytest.mark.asyncio
async def test_error_handling(event_bus):
    """Test la gestion des erreurs dans les listeners"""
    async def faulty_listener(event):
        raise Exception("Test error")
    
    await event_bus.subscribe("error_event", faulty_listener)
    # Ne devrait pas lever d'exception
    await event_bus.emit(Event(type="error_event", data="data"))

@pytest.mark.asyncio
async def test_game_event_sequence(event_bus):
    """Test la séquence d'événements de jeu"""
    events_sequence = []
    
    async def game_listener(event):
        events_sequence.append(event.type)
    
    # S'abonner à tous les événements de jeu
    for event_type in ["dice_roll", "content_update", "stats_update"]:
        await event_bus.subscribe(event_type, game_listener)
    
    # Émettre une séquence d'événements
    await event_bus.emit(Event(type="dice_roll", data={"result": 6}))
    await event_bus.emit(Event(type="content_update", data={"section": 1}))
    await event_bus.emit(Event(type="stats_update", data={"health": 10}))
    
    # Vérifier l'ordre des événements
    assert events_sequence == ["dice_roll", "content_update", "stats_update"]
    assert len(event_bus.history) == 3

@pytest.mark.asyncio
async def test_event_filtering(event_bus):
    """Test le filtrage des événements par type"""
    dice_events = []
    content_events = []
    
    async def dice_listener(event):
        dice_events.append(event)
    
    async def content_listener(event):
        content_events.append(event)
    
    await event_bus.subscribe("dice_roll", dice_listener)
    await event_bus.subscribe("content_update", content_listener)
    
    # Émettre différents types d'événements
    await event_bus.emit(Event(type="dice_roll", data={"result": 6}))
    await event_bus.emit(Event(type="content_update", data={"section": 1}))
    await event_bus.emit(Event(type="stats_update", data={"health": 10}))
    
    assert len(dice_events) == 1
    assert len(content_events) == 1
    assert dice_events[0].data["result"] == 6
    assert content_events[0].data["section"] == 1

@pytest.mark.asyncio
async def test_concurrent_events(event_bus):
    """Test la gestion d'événements concurrents"""
    import asyncio
    
    processed_events = []
    
    async def slow_listener(event):
        await asyncio.sleep(0.1)  # Simuler un traitement lent
        processed_events.append(event.type)
    
    await event_bus.subscribe("concurrent_test", slow_listener)
    
    # Émettre plusieurs événements rapidement
    events = [Event(type="concurrent_test", data={"id": i}) for i in range(3)]
    await asyncio.gather(*[event_bus.emit(event) for event in events])
    
    # Attendre que tous les événements soient traités
    await asyncio.sleep(0.3)
    
    assert len(processed_events) == 3
    assert len(event_bus.history) == 3

@pytest.mark.asyncio
async def test_event_data_integrity(event_bus):
    """Test l'intégrité des données d'événement"""
    received_events = []
    
    async def data_listener(event):
        received_events.append(event)
    
    complex_data = {
        "stats": {"strength": 10, "agility": 8},
        "inventory": ["sword", "shield"],
        "position": {"x": 100, "y": 200}
    }
    
    await event_bus.subscribe("game_state", data_listener)
    await event_bus.emit(Event(type="game_state", data=complex_data))
    
    assert len(received_events) == 1
    received_data = received_events[0].data
    assert received_data["stats"]["strength"] == 10
    assert received_data["inventory"] == ["sword", "shield"]
    assert received_data["position"]["x"] == 100
