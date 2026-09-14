from datetime import datetime, timezone
from pydantic import BaseModel, Field

class SensorReading(BaseModel):
    node_id: str = Field(default="NODE_01", min_length=1, max_length=50)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mq2: float = Field(ge=0.0, le=1.0)
    mq7: float = Field(ge=0.0, le=1.0)
    flame: int = Field(ge=0, le=1)
    temperature: float = Field(ge=-20.0, le=150.0)
    humidity: float = Field(ge=0.0, le=100.0)
    pir: int = Field(ge=0, le=1)
    mmwave: int = Field(ge=0, le=1)
