import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import threading
import time
from sqlalchemy.orm import Session
from collections import defaultdict

from . import crud, schemas
from .database import SessionLocal

processing_thread = None
stop_event = threading.Event()

live_stats_cache = defaultdict(lambda: {"total_in": 0, "total_out": 0})
latest_frame_data_cache = defaultdict(list)

FRAME_SKIP_INTERVAL = 10

def video_processing_loop(area_id: int):
    """
    The main loop that captures video, performs detection/tracking, and logs events.
    """
    print(f"Starting video processing for area_id: {area_id}...")

    db: Session = SessionLocal()
    area = crud.get_area(db, area_id=area_id)
    if not area:
        print(f"Error: Area with ID {area_id} not found in database.")
        db.close()
        return
        
    polygon_points = np.array(area.coordinates, np.int32)
    db.close()
    
    try:
        model = YOLO('yolo_model/yolo11s.pt')
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        return

    stream_url = 'https://cctvjss.jogjakota.go.id/malioboro/Malioboro_10_Kepatihan.stream/playlist.m3u8'
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("Error: Cannot open stream.")
        return

    track_history = defaultdict(lambda: {'is_inside': False})

    frame_counter = 0
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Stream end or error. Attempting to reconnect...")
            time.sleep(5)
            cap.release()
            cap = cv2.VideoCapture(stream_url)
            continue

        frame_counter += 1

        if frame_counter % FRAME_SKIP_INTERVAL != 0:
            continue

        try:
            results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=0, conf=0.3, verbose=False)
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        except (AttributeError, IndexError):
            continue

        current_frame_detections = []
        db: Session = SessionLocal()
        
        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = box
            person_anchor_point = (int((x1 + x2) / 2), int(y2))
            is_inside_now = cv2.pointPolygonTest(polygon_points, person_anchor_point, False) >= 0

            current_frame_detections.append({
                "box": box.tolist(),
                "track_id": int(track_id),
                "is_inside": is_inside_now
            })

            was_inside_before = track_history[track_id]['is_inside']

            event_to_log = None
            if is_inside_now and not was_inside_before:
                event_to_log = schemas.CountingEventCreate(event_type='in', track_id=int(track_id), area_id=area_id)
                print(f"ID {track_id} ENTERED Area {area_id}")
                live_stats_cache[area_id]["total_in"] += 1

            elif not is_inside_now and was_inside_before:
                event_to_log = schemas.CountingEventCreate(event_type='out', track_id=int(track_id), area_id=area_id)
                print(f"ID {track_id} EXITED Area {area_id}")
                live_stats_cache[area_id]["total_out"] += 1

            if event_to_log:
                crud.create_counting_event(db=db, event=event_to_log)

            track_history[track_id]['is_inside'] = is_inside_now
        
        db.close()

        latest_frame_data_cache[area_id] = current_frame_detections
        
    cap.release()
    print(f"Stopped video processing for area_id: {area_id}.")

def start_processing_thread(area_id: int):
    """Starts the background thread if it's not already running."""
    global processing_thread
    if processing_thread is None or not processing_thread.is_alive():
        stop_event.clear()
        processing_thread = threading.Thread(target=video_processing_loop, args=(area_id,), daemon=True)
        processing_thread.start()
        print("Video processing thread started.")

def stop_processing_thread():
    """Stops the background thread."""
    global processing_thread
    if processing_thread and processing_thread.is_alive():
        stop_event.set()
        processing_thread.join()
        processing_thread = None
        print("Video processing thread stopped.")