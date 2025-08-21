from typing import List
from sqlalchemy.orm import Session
from . import models, schemas
import datetime

def get_area(db: Session, area_id: int):
    return db.query(models.Area).filter(models.Area.id == area_id).first()

def get_area_by_name(db: Session, name: str):
    return db.query(models.Area).filter(models.Area.name == name).first()

def get_areas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Area).offset(skip).limit(limit).all()

def create_area(db: Session, area: schemas.AreaCreate):
    db_area = models.Area(name=area.name, coordinates=area.coordinates)
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

def update_area_coordinates(db: Session, area_id: int, coordinates: List[tuple]):
    db_area = get_area(db, area_id)
    if db_area:
        db_area.coordinates = coordinates
        db.commit()
        db.refresh(db_area)
    return db_area

def create_counting_event(db: Session, event: schemas.CountingEventCreate):
    db_event = models.CountingEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_counting_history(db: Session, area_id: int, start_time: datetime.datetime, end_time: datetime.datetime, skip: int = 0, limit: int = 100):
    return db.query(models.CountingEvent).filter(
        models.CountingEvent.area_id == area_id,
        models.CountingEvent.timestamp >= start_time,
        models.CountingEvent.timestamp <= end_time
    ).order_by(models.CountingEvent.timestamp.desc()).offset(skip).limit(limit).all()

def get_live_stats(db: Session, area_id: int):
    total_in = db.query(models.CountingEvent).filter(
        models.CountingEvent.area_id == area_id,
        models.CountingEvent.event_type == 'in'
    ).count()
    
    total_out = db.query(models.CountingEvent).filter(
        models.CountingEvent.area_id == area_id,
        models.CountingEvent.event_type == 'out'
    ).count()
    
    return schemas.LiveStats(
        total_in=total_in, 
        total_out=total_out, 
        current_inside=total_in - total_out
    )