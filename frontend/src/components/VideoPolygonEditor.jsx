import React, { useRef, useEffect, useState, useCallback } from 'react';
import Hls from 'hls.js';

const API_BASE_URL = 'http://127.0.0.1:8000';
const STREAM_URL = 'https://cctvjss.jogjakota.go.id/malioboro/Malioboro_10_Kepatihan.stream/playlist.m3u8';

const drawDetectionBoxes = (ctx, boxes, videoWidth, videoHeight) => {
  const canvasWidth = ctx.canvas.width;
  const canvasHeight = ctx.canvas.height;

  boxes.forEach(det => {
    const [x1, y1, x2, y2] = det.box;
    const isInside = det.is_inside;

    const scaledX1 = (x1 / videoWidth) * canvasWidth;
    const scaledY1 = (y1 / videoHeight) * canvasHeight;
    const scaledWidth = ((x2 - x1) / videoWidth) * canvasWidth;
    const scaledHeight = ((y2 - y1) / videoHeight) * canvasHeight;

    ctx.strokeStyle = isInside ? '#FF4136' : '#0074D9';
    ctx.lineWidth = 2;
    ctx.strokeRect(scaledX1, scaledY1, scaledWidth, scaledHeight);

    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = '14px Arial';
    ctx.fillText(`ID: ${det.track_id}`, scaledX1, scaledY1 - 5);
  });
};


const VideoPolygonEditor = ({ areaId }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [points, setPoints] = useState([]);
  const [areaName, setAreaName] = useState('');
  const [detectionBoxes, setDetectionBoxes] = useState([]); // NEW STATE FOR BBOXES

  const drawPolygon = useCallback((ctx, currentPoints) => {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    if (currentPoints.length === 0) return;
    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 3;
    ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
    ctx.beginPath();
    ctx.moveTo(currentPoints[0].x, currentPoints[0].y);
    for (let i = 1; i < currentPoints.length; i++) {
      ctx.lineTo(currentPoints[i].x, currentPoints[i].y);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.fill();
    ctx.fillStyle = '#FF0000';
    currentPoints.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, 2 * Math.PI);
      ctx.fill();
    });
  }, []);

  useEffect(() => {
    const fetchAreaConfig = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/config/area/${areaId}`);
            const data = await response.json();
            const scaledPoints = data.coordinates.map(([x, y]) => ({
                x: x / 1920 * 960,
                y: y / 1080 * 540
            }));
            setPoints(scaledPoints);
            setAreaName(data.name);
        } catch (error) {
            console.error("Failed to fetch area config:", error);
        }
    };
    fetchAreaConfig();
  }, [areaId]);

  useEffect(() => {
    const video = videoRef.current;
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(STREAM_URL);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(e => console.error("Autoplay was prevented:", e));
      });
      return () => hls.destroy();
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = STREAM_URL;
    }
  }, []);

  useEffect(() => {
    const fetchDetections = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/detections/live?area_id=${areaId}`);
            if (response.ok) {
                const data = await response.json();
                setDetectionBoxes(data);
            }
        } catch (error) {
            console.error("Failed to fetch detections:", error);
        }
    };
    const intervalId = setInterval(fetchDetections, 150);
    return () => clearInterval(intervalId);
  }, [areaId]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    drawPolygon(ctx, points);

    drawDetectionBoxes(ctx, detectionBoxes, 1920, 1080);

  }, [points, detectionBoxes, drawPolygon]);

  const handleCanvasClick = (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    setPoints([...points, { x, y }]);
  };

  const handleClear = () => {
    setPoints([]);
  };

  const handleSave = async () => {
    if (points.length < 3) {
      alert("A polygon must have at least 3 points.");
      return;
    }
    const originalScalePoints = points.map(p => [
      Math.round(p.x / 960 * 1920),
      Math.round(p.y / 540 * 1080)
    ]);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/config/area/${areaId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: areaName, coordinates: originalScalePoints })
        });
        if (!response.ok) throw new Error('Failed to save polygon');
        alert('Polygon saved successfully! Please restart the backend server to apply changes.');
    } catch (error) {
        console.error("Save failed:", error);
        alert('Error saving polygon.');
    }
  };


  return (
    <div>
      <h1>CCTV Feed</h1>
      <div className="video-container">
        <video ref={videoRef} muted playsInline autoPlay style={{ backgroundColor: 'black' }} />
        <canvas
          ref={canvasRef}
          width="960"
          height="540"
          onClick={handleCanvasClick}
        />
      </div>
      <div className="controls">
        <button onClick={handleSave}>Save Polygon</button>
        <button onClick={handleClear}>Clear Points</button>
        <button onClick={() => setPoints(points.slice(0, -1))}>Undo Last Point</button>
      </div>
      <p>Click on the video to add polygon points. Restart the backend to apply changes after saving.</p>
      <div className='warning'>⚠️ Currently there's an issue to sync the model inference with live video footage so the bounding box appear out-of-sync ⚠️</div>
    </div>
  );
};

export default VideoPolygonEditor;