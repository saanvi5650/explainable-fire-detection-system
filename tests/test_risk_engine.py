from backend.schemas import SensorReading
from backend.risk_engine import baseline_prediction, apply_adaptive_logic

def sample(**changes):
    data = {
        "mq2": 0.12, "mq7": 0.10, "flame": 0,
        "temperature": 28, "humidity": 55, "pir": 0, "mmwave": 0
    }
    data.update(changes)
    return SensorReading(**data)

def test_safe_room_is_safe():
    reading = sample()
    tier, *_ = baseline_prediction(reading, [reading])
    assert tier == "Safe"

def test_flame_is_at_least_critical():
    reading = sample(flame=1)
    tier, *_ = baseline_prediction(reading, [reading])
    assert tier in {"Critical", "Evacuate"}

def test_occupancy_escalates_critical():
    reading = sample(mq2=.8, mq7=.7, temperature=55, pir=1)
    adjusted, _, occupied, _ = apply_adaptive_logic("Critical", .85, reading)
    assert occupied is True
    assert adjusted == "Evacuate"

def test_empty_room_never_downgrades_strong_fire_to_safe():
    reading = sample(mq2=.85, mq7=.75, temperature=60)
    adjusted, *_ = apply_adaptive_logic("Critical", .9, reading)
    assert adjusted in {"Critical", "Evacuate"}
