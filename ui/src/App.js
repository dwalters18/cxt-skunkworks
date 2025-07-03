// ui/src/App.js

import React from 'react';
import TMSDashboard from './components/TMSDashboard';
import './App.css';

function App() {
  return (
      <div className="App">
        <header className="App-header">
          <h1>The Next Generation of Logistics & Courier Software</h1>
          <h4>AI-powered. Autonomous. Built for the future of delivery.</h4>
          <p>Intelligent last-mile, route, and on-demand shipment orchestration that adapts and scales with your operation—empowering drivers, dispatchers, and clients with precision, speed, and ease.</p>
        </header>
        <TMSDashboard />
      </div>
  );
}

export default App;
