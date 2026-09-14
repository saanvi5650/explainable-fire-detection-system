# ESP32 to software data contract

Publish one JSON object to firenode/NODE_01/data every 2 to 5 seconds.

Required fields:
- node_id: string
- timestamp: ISO 8601 string
- mq2 and mq7: normalized 0 to 1 until calibrated
- flame: 0 or 1
- temperature: degrees Celsius
- humidity: percentage
- pir and mmwave: 0 or 1

The bridge publishes the decision to firenode/NODE_01/risk with tier, confidence, occupancy and explanation.

Strong fire evidence is never downgraded merely because the zone is unoccupied.
