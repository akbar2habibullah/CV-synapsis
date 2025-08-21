from pydantic import BaseModel
from typing import List, Tuple
import datetime

class CountingEventBase(BaseModel):
    event_type: str
    track_id: int
    area_id: int

class CountingEventCreate(CountingEventBase):
    pass

class CountingEvent(CountingEventBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        orm_mode = True
class AreaBase(BaseModel):
    name: str
    coordinates: List[Tuple[int, int]]

class AreaCreate(AreaBase):
    pass

class Area(AreaBase):
    id: int

    class Config:
        orm_mode = True

class LiveStats(BaseModel):
    total_in: int
    total_out: int
    current_inside: int

class HistoryStats(BaseModel):
    events: List[CountingEvent]

class DetectionBox(BaseModel):
    box: List[int]
    track_id: int
    is_inside: bool