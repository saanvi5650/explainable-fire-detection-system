import sqlite3
from .config import DB_PATH

def connect():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes(
            node_id TEXT PRIMARY KEY,
            location TEXT DEFAULT 'Demo Room',
            zone_type TEXT DEFAULT 'indoor',
            installed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sensor_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            mq2 REAL NOT NULL,
            mq7 REAL NOT NULL,
            flame INTEGER NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            pir INTEGER NOT NULL,
            mmwave INTEGER NOT NULL,
            occupied INTEGER NOT NULL,
            raw_tier TEXT NOT NULL,
            risk_tier TEXT NOT NULL,
            risk_score REAL NOT NULL,
            confidence REAL NOT NULL,
            prediction_source TEXT NOT NULL,
            explanation_method TEXT NOT NULL,
            explanation TEXT NOT NULL,
            latency_ms REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS explanations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            feature_name TEXT NOT NULL,
            contribution REAL NOT NULL,
            FOREIGN KEY(event_id) REFERENCES sensor_events(id)
        );
        """)

def save_event(reading, result, latency_ms):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO nodes(node_id) VALUES(?)", (reading.node_id,))
        cursor = db.execute("""
            INSERT INTO sensor_events(
                node_id,timestamp,mq2,mq7,flame,temperature,humidity,pir,mmwave,
                occupied,raw_tier,risk_tier,risk_score,confidence,prediction_source,
                explanation_method,explanation,latency_ms
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            reading.node_id, reading.timestamp.isoformat(), reading.mq2, reading.mq7,
            reading.flame, reading.temperature, reading.humidity, reading.pir,
            reading.mmwave, int(result["occupied"]), result["raw_tier"],
            result["adjusted_tier"], result["risk_score"], result["confidence"],
            result["prediction_source"], result["explanation_method"],
            result["explanation"], latency_ms
        ))
        event_id = cursor.lastrowid
        db.executemany(
            "INSERT INTO explanations(event_id,feature_name,contribution) VALUES(?,?,?)",
            [(event_id, item["feature"], item["contribution"]) for item in result["contributors"]]
        )
        return event_id

def _event_with_explanations(db, row):
    if row is None:
        return None
    event = dict(row)
    event["occupied"] = bool(event["occupied"])
    event["contributors"] = [
        dict(x) for x in db.execute(
            "SELECT feature_name AS feature, contribution FROM explanations WHERE event_id=? ORDER BY contribution DESC",
            (event["id"],)
        ).fetchall()
    ]
    return event

def latest(node_id):
    with connect() as db:
        row = db.execute(
            "SELECT * FROM sensor_events WHERE node_id=? ORDER BY id DESC LIMIT 1",
            (node_id,)
        ).fetchone()
        return _event_with_explanations(db, row)

def history(node_id, limit=100):
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM sensor_events WHERE node_id=? ORDER BY id DESC LIMIT ?",
            (node_id, limit)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

def nodes():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM nodes ORDER BY node_id").fetchall()]

def metrics():
    with connect() as db:
        rows = db.execute("SELECT risk_tier, latency_ms FROM sensor_events").fetchall()
    latencies = sorted(float(r["latency_ms"]) for r in rows)
    counts = {tier: 0 for tier in ("Safe", "Warning", "Critical", "Evacuate")}
    for row in rows:
        counts[row["risk_tier"]] = counts.get(row["risk_tier"], 0) + 1
    if not latencies:
        return {"total_predictions": 0, "tier_counts": counts, "average_latency_ms": 0, "p95_latency_ms": 0}
    p95_index = min(len(latencies)-1, int(0.95 * len(latencies)))
    return {
        "total_predictions": len(latencies),
        "tier_counts": counts,
        "average_latency_ms": round(sum(latencies)/len(latencies), 3),
        "p95_latency_ms": round(latencies[p95_index], 3)
    }
