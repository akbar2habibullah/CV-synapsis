from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    coordinates = Column(JSON, nullable=False)
    
    counting_events = relationship("CountingEvent", back_populates="area")

class CountingEvent(Base):
    __tablename__ = "counting_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_type = Column(String)
    track_id = Column(Integer)
    
    area_id = Column(Integer, ForeignKey("areas.id"))
    area = relationship("Area", back_populates="counting_events")