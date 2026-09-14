import argparse
import math
import random
import time
from datetime import datetime, timezone
import requests

def reading_for(scenario, step, node_id):
    progress = min(1.0, step / 35.0)
    n = lambda scale: random.uniform(-scale, scale)
    occupied = scenario == "occupied_fire"

    if scenario == "safe":
        mq2, mq7, temp, humidity, flame = 0.14+n(.025), 0.11+n(.02), 28+n(.5), 55+n(2), 0
        occupied = bool((step // 12) % 2)
    elif scenario == "cooking":
        mq2, mq7 = 0.20+0.34*progress+n(.025), 0.13+0.10*progress+n(.02)
        temp, humidity, flame = 29+5*progress+n(.5), 53+n(2), 0
        occupied = True
    elif scenario == "smouldering":
        mq2, mq7 = 0.25+0.55*progress+n(.025), 0.20+0.48*progress+n(.025)
        temp, humidity, flame = 30+20*progress+n(.7), 50-8*progress+n(1.5), 0
    else:
        mq2, mq7 = 0.30+0.63*progress+n(.02), 0.25+0.59*progress+n(.02)
        temp, humidity = 31+33*progress+n(.8), 49-13*progress+n(1.5)
        flame = int(progress > .55)
        occupied = scenario == "occupied_fire"

    return {
        "node_id": node_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mq2": round(max(0, min(1, mq2)), 4),
        "mq7": round(max(0, min(1, mq7)), 4),
        "flame": flame,
        "temperature": round(temp, 2),
        "humidity": round(max(0, min(100, humidity)), 2),
        "pir": int(occupied and random.random() > .2),
        "mmwave": int(occupied)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["safe","cooking","smouldering","fire","occupied_fire"], default="safe")
    parser.add_argument("--node", default="NODE_01")
    parser.add_argument("--readings", type=int, default=80)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/readings")
    args = parser.parse_args()

    print(f"Starting {args.scenario} scenario for {args.node}")
    for step in range(args.readings):
        payload = reading_for(args.scenario, step, args.node)
        try:
            response = requests.post(args.url, json=payload, timeout=5)
            response.raise_for_status()
            result = response.json()
            print(
                f'{step+1:03d} tier={result["adjusted_tier"]:<9} '
                f'window={result["window_size"]:02d}/40 '
                f'source={result["prediction_source"]:<8} '
                f'latency={result["latency_ms"]:.2f}ms'
            )
        except requests.RequestException as exc:
            print("Server request failed:", exc)
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
