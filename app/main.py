from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
from fastapi.middleware.cors import CORSMiddleware

from . import crud, models, schemas, processing
from .database import engine, get_db, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Synapsis AI Challenge - People Counting",
    description="An API for object detection, tracking, and people counting in a defined polygon area.",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """
    - Checks for a default area and creates one if none exist.
    - Starts the background video processing task.
    """
    db = SessionLocal()
    default_area = crud.get_area_by_name(db, name="Malioboro Gate")
    if not default_area:
        print("Default area not found. Creating one...")
        default_coords = [(914, 949), (1875, 832), (1415, 681), (1438, 346), (691, 264), (669, 687), (915, 950)]
        area_schema = schemas.AreaCreate(name="Malioboro Gate", coordinates=default_coords)
        crud.create_area(db, area=area_schema)
        default_area = crud.get_area_by_name(db, name="Malioboro Gate")

    print("NOTE: To apply polygon changes from the API, you must restart the application.")
    processing.start_processing_thread(area_id=default_area.id)
    db.close()

@app.on_event("shutdown")
def on_shutdown():
    """Stops the background thread gracefully."""
    processing.stop_processing_thread()

@app.post("/api/config/area", response_model=schemas.Area, status_code=201)
def create_new_area(area: schemas.AreaCreate, db: Session = Depends(get_db)):
    """
    (Optional) Create a new polygon area for detection.
    Note: The system currently only processes one area at a time (the one started at launch).
    A more advanced system would manage multiple processing threads.
    """
    db_area = crud.get_area_by_name(db, name=area.name)
    if db_area:
        raise HTTPException(status_code=400, detail="Area name already registered")
    return crud.create_area(db=db, area=area)

@app.get("/api/config/area/{area_id}", response_model=schemas.Area)
def read_area(area_id: int, db: Session = Depends(get_db)):
    db_area = crud.get_area(db, area_id=area_id)
    if db_area is None:
        raise HTTPException(status_code=404, detail="Area not found")
    return db_area

@app.put("/api/config/area/{area_id}", response_model=schemas.Area)
def update_area(area_id: int, new_coords: schemas.AreaBase, db: Session = Depends(get_db)):
    """
    Update an existing area's polygon coordinates.
    NOTE: A server restart is required for the video processor to use the new coordinates.
    """
    db_area = crud.get_area(db, area_id=area_id)
    if db_area is None:
        raise HTTPException(status_code=404, detail="Area not found")
    return crud.update_area_coordinates(db=db, area_id=area_id, coordinates=new_coords.coordinates)

@app.get("/api/stats/live", response_model=schemas.LiveStats)
def get_live_statistics(area_id: int = 1):
    """
    Returns the most recent count of people who have entered and exited the area.
    This uses a simple in-memory cache for speed, updated by the background worker.
    """
    stats = processing.live_stats_cache.get(area_id)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"No live stats available for area_id {area_id}. Is processing running?")
    
    return schemas.LiveStats(
        total_in=stats["total_in"],
        total_out=stats["total_out"],
        current_inside=stats["total_in"] - stats["total_out"]
    )

@app.get("/api/stats/", response_model=List[schemas.CountingEvent])
def get_historical_statistics(
    area_id: int = 1,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Displays the history of 'in' and 'out' events for an area.
    Supports time range filtering and pagination.
    """
    if end_time is None:
        end_time = datetime.datetime.utcnow()
    if start_time is None:
        start_time = end_time - datetime.timedelta(days=1)
        
    events = crud.get_counting_history(db, area_id=area_id, start_time=start_time, end_time=end_time, skip=skip, limit=limit)
    return events

@app.get("/api/detections/live", response_model=List[schemas.DetectionBox])
def get_live_detections(area_id: int = 1):
    """
    Returns the most recent list of detected bounding boxes for a given area.
    This data is polled by the frontend to simulate a live view.
    """
    detections = processing.latest_frame_data_cache.get(area_id, [])
    return detections