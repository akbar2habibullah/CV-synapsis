import React from 'react';
import StatsDisplay from './components/StatsDisplay';
import VideoPolygonEditor from './components/VideoPolygonEditor';
import './App.css';

function App() {
  const AREA_ID_TO_MANAGE = 1;

  return (
    <div className="App">
      <div className="container">
        <VideoPolygonEditor areaId={AREA_ID_TO_MANAGE} />
        <StatsDisplay areaId={AREA_ID_TO_MANAGE} />
      </div>
    </div>
  );
}

export default App;