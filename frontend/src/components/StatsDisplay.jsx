import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000';

const StatsDisplay = ({ areaId }) => {
  const [stats, setStats] = useState({ total_in: 0, total_out: 0, current_inside: 0 });
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/stats/live?area_id=${areaId}`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setStats(data);
        setError(null);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
        setError("Could not connect to API.");
      }
    };

    fetchStats();
    const intervalId = setInterval(fetchStats, 3000);

    return () => clearInterval(intervalId);
  }, [areaId]);

  return (
    <div className="stats-panel">
      <h2>Live Statistics (Area {areaId})</h2>
      {error ? <p style={{ color: 'red' }}>{error}</p> : (
        <>
          <p className="stat-item">Total In: <span>{stats.total_in}</span></p>
          <p className="stat-item">Total Out: <span>{stats.total_out}</span></p>
          <p className="stat-item">Currently Inside: <span>{stats.current_inside}</span></p>
        </>
      )}
    </div>
  );
};

export default StatsDisplay;