TIER_ORDER = {"Safe": 0, "Warning": 1, "Critical": 2, "Evacuate": 3}

def baseline_prediction(reading, window):
    gas_score = min(1.0, 0.55 * reading.mq2 + 0.45 * reading.mq7)
    temperature_score = min(1.0, max(0.0, (reading.temperature - 30.0) / 35.0))
    flame_score = float(reading.flame)

    trend_score = 0.0
    if len(window) >= 5:
        old = window[-5]
        gas_delta = max(0.0, (reading.mq2 + reading.mq7) - (old.mq2 + old.mq7))
        temp_delta = max(0.0, reading.temperature - old.temperature) / 20.0
        trend_score = min(1.0, 0.7 * gas_delta + 0.3 * temp_delta)

    score = min(1.0, 0.32 * gas_score + 0.23 * temperature_score + 0.38 * flame_score + 0.07 * trend_score)

    if score < 0.22:
        tier = "Safe"
    elif score < 0.45:
        tier = "Warning"
    elif score < 0.72:
        tier = "Critical"
    else:
        tier = "Evacuate"

    if reading.flame and gas_score > 0.45:
        tier = "Evacuate"
    elif reading.flame:
        tier = "Critical"
    elif reading.mq2 > 0.70 and reading.mq7 > 0.60:
        tier = "Critical"

    probabilities = {name: 0.02 for name in TIER_ORDER}
    probabilities[tier] = 0.94
    contributions = {
        "Smoke/Gas": 0.32 * gas_score,
        "Temperature": 0.23 * temperature_score,
        "Flame": 0.38 * flame_score,
        "Rising trend": 0.07 * trend_score
    }
    return tier, score, probabilities, contributions

def apply_adaptive_logic(raw_tier, confidence, reading):
    occupied = bool(reading.pir or reading.mmwave)
    adjusted = raw_tier
    reason = None

    strong_fire = reading.flame == 1 and (reading.mq2 > 0.45 or reading.temperature > 42)
    strong_gas = reading.mq2 > 0.72 and reading.mq7 > 0.62

    if strong_fire or strong_gas:
        adjusted = "Evacuate" if occupied else "Critical"
        reason = "Strong multi-sensor fire evidence"
    elif raw_tier == "Critical" and occupied:
        adjusted = "Evacuate"
        reason = "Critical fire risk with confirmed occupancy"

    cooking_signature = (
        reading.flame == 0 and reading.mq2 > 0.35 and
        reading.mq7 < 0.35 and reading.temperature < 42
    )
    if raw_tier == "Warning" and not occupied and cooking_signature:
        confidence = max(0.50, confidence * 0.90)
        reason = "Possible cooking-smoke signature in an unoccupied zone"

    return adjusted, round(float(confidence), 4), occupied, reason

def normalise_contributions(values):
    positive = {key: abs(float(value)) for key, value in values.items()}
    total = sum(positive.values())
    if total <= 0:
        return []
    return [
        {"feature": key, "contribution": round(value * 100.0 / total, 2)}
        for key, value in sorted(positive.items(), key=lambda item: item[1], reverse=True)
    ]
