# Synapsis AI Engineer Challenge: People Counting System

This project is a solution for the Synapsis AI Engineer Challenge. It implements a complete system for object detection, tracking, and people counting within a user-defined polygon area from a live video feed. The system features a FastAPI backend, a React frontend dashboard, and uses YOLOv8 for real-time AI inference.

## Features

*   **Live CCTV Streaming**: Ingests and displays an HLS video stream in the web dashboard.
*   **Real-time People Detection & Tracking**: Uses YOLOv8 with ByteTrack to detect and assign unique, persistent IDs to people in the video feed.
*   **Dynamic Polygon Area**: Users can draw, modify, and save a polygonal "high-risk" area directly on the video feed via the UI.
*   **Live Bounding Box Visualization**: Overlays detected bounding boxes and track IDs onto the live video, color-coded to indicate if a person is inside or outside the defined area.
*   **Real-time In/Out Statistics**: Accurately counts and displays the number of people entering, exiting, and currently inside the polygon.
*   **RESTful API**: A robust FastAPI backend provides endpoints for statistics, live detections, and area configuration.
*   **Performance Optimized**: Implements a frame-skipping mechanism to reduce computational load while maintaining tracking accuracy.

## System Design & Flow

The application is architected with a clear separation of concerns between the backend processing and the frontend visualization.



1.  **Video Processing Worker (`app/processing.py`)**: A background thread continuously reads frames from the live HLS stream. It performs inference using YOLOv8 on a configurable interval (e.g., every 15th frame) to detect and track people.
2.  **In-Memory Cache**: The worker updates two in-memory caches: one for the latest bounding box data and another for the live in/out counts. This allows for fast, low-latency API responses.
3.  **Database (`SQLite` via `SQLAlchemy`)**: When a person crosses the polygon boundary (enters or exits), the worker logs this event in a persistent SQLite database for historical analysis.
4.  **FastAPI Backend (`app/main.py`)**: Exposes REST API endpoints. The frontend polls these endpoints to get live statistics and bounding box data. It also provides endpoints to manage the polygon area configuration stored in the database.
5.  **React Frontend**: A web-based dashboard that consumes the API. It uses `hls.js` to render the video, polls the backend for data, and uses an HTML Canvas to draw the polygon and real-time bounding boxes over the video feed.

### Database Schema

*   **`areas` table**: Stores the configuration for each detection area.
    *   `id` (PK), `name` (String), `coordinates` (JSON)
*   **`counting_events` table**: Logs every time a person enters or exits a defined area.
    *   `id` (PK), `timestamp` (DateTime), `event_type` (String: "in"/"out"), `track_id` (Integer), `area_id` (FK)

The relation is **One-to-Many**: One `area` can have many `counting_events`.

---

## Setup and Installation

### Prerequisites
*   Python 3.8+
*   Node.js 16+ and npm
*   Git

### Steps
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-folder>
    ```

2.  **Backend Setup:**
    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Download a YOLOv8 model (e.g., yolov8s.pt) and place it in the yolo_model/ directory.
    ```

3.  **Frontend Setup:**
    ```bash
    # Navigate to the frontend directory
    cd frontend

    # Install Node.js dependencies
    npm install
    ```

---

## How to Run

You will need two separate terminal windows.

1.  **Terminal 1: Start the FastAPI Server**
    From the project's **root directory**, run:
    ```bash
    uvicorn app.main:app --reload
    ```
    The backend API will be available at `http://127.0.0.1:8000`.

2.  **Terminal 2: Start the React Frontend**
    From the `frontend/` directory, run:
    ```bash
    npm run dev
    ```
    The web dashboard will be available at `http://localhost:5173` (or the port specified in the terminal).

3.  **Access the Application**
    *   Open your browser and navigate to **`http://localhost:5173`** to see the live dashboard.
    *   To view the API documentation, navigate to `http://127.0.0.1:8000/docs`.

---

## API Endpoints

### `GET /api/stats/live`
Returns the latest "in", "out", and "current" counts for a given area.
*   **Example**: `curl http://127.0.0.1:8000/api/stats/live?area_id=1`

### `GET /api/detections/live`
Returns a list of the most recently detected bounding boxes and their status.
*   **Example**: `curl http://127.0.0.1:8000/api/detections/live?area_id=1`
*   **Response Body**:
    ```json
    [
      { "box": [x1, y1, x2, y2], "track_id": 101, "is_inside": true },
      { "box": [x1, y1, x2, y2], "track_id": 102, "is_inside": false }
    ]
    ```

### `PUT /api/config/area/{area_id}`
Updates the coordinates of an existing polygon area.
*   **Note**: Requires a backend restart for the changes to take effect in the processing thread.
*   **Request Body**:
    ```json
    {
      "name": "Malioboro Gate",
      "coordinates": [[914, 949], [1875, 832], ...]
    }
    ```

### `GET /api/stats/`
Returns a historical list of all "in" and "out" events, with support for time-based filtering and pagination.

---

## Challenge Checklist

1.  **Desain Database (Done)**
    *   **Note**: A relational database schema using SQLAlchemy and SQLite is designed and implemented. It features an `areas` table for dynamic polygon configuration and a `counting_events` table for logging historical data, enabling efficient querying.

2.  **Pengumpulan Dataset (Done)**
    *   **Note**: The application successfully uses the live CCTV stream `Malioboro_10_Kepatihan.stream` as its data source, as specified in the challenge.

3.  **Object Detection & Tracking (Done)**
    *   **Note**: The core logic uses the powerful YOLOv8 model with the ByteTrack tracker for robust detection and tracking. Includes performance optimization by processing every Nth frame to balance real-time feedback with computational load.

4.  **Counting & Polygon Area (Done)**
    *   **Note**: The system accurately counts entries and exits based on a person's anchor point crossing the boundary of a polygon. The polygon itself is fully dynamic and can be configured via the web UI and API.

5.  **Prediksi (Forecasting) (X)**
    *   **Note**: Forecasting was not implemented as the challenge's core focus was on detection, tracking, counting, and system integration.

6.  **Integrasi API & Frontend (Done)**
    *   **Note**: A complete FastAPI backend serves all required data via a well-defined REST API. Additionally, a full-featured React web dashboard has been developed to provide a user-friendly interface for visualizing the live video, statistics, bounding boxes, and for dynamically editing the detection area.

7.  **Deployment (X)**
    *   **Note**: Containerization with Docker was not implemented to keep the submission focused on the core AI and backend logic, as it was listed as an optional plus. This `README` provides clear, comprehensive instructions for a local setup.