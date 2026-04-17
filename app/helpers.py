import random

RESPONSES = [
    "heavy traffic on highway",
    "vehicle breakdown, need assistance",
    "all clear, on schedule",
    "bad weather, road flooded",
    "minor delay, fuel stop",
    "route blocked, taking detour",
]

RISK_WEIGHTS = {
    "breakdown": 0.9,
    "flooded":   0.85,
    "blocked":   0.7,
    "traffic":   0.5,
    "detour":    0.45,
    "delay":     0.3,
    "clear":     0.1,
}

def process_driver_response(text: str) -> dict:
    text_lower = text.lower()
    for keyword, score in RISK_WEIGHTS.items():
        if keyword in text_lower:
            status     = "critical" if score >= 0.7 else "warning" if score >= 0.4 else "ok"
            confidence = round(0.75 + random.uniform(0, 0.2), 2)
            return {"status": status, "reason": keyword, "confidence": confidence}
    return {"status": "ok", "reason": "unknown", "confidence": 0.5}

def calculate_risk(data: dict) -> dict:
    base   = RISK_WEIGHTS.get(data.get("reason", ""), 0.2)
    conf   = data.get("confidence", 0.5)
    score = round(base * 0.7 + conf * 0.3, 3)
    decision = "ESCALATE" if score >= 0.6 else "MONITOR" if score >= 0.3 else "RESOLVE"
    return {"score": score, "decision": decision}
