// ui/src/App.js

import React from 'react';
import TMSDashboard from './components/TMSDashboard';
import './App.css';

function App() {
  return (
      <div className="App">
        <header className="App-header">
          <h1>TMS Event-Driven Platform</h1>
          <p>Transportation Management System with Real-time Event Processing</p>
        </header>
        <TMSDashboard />
      </div>
  );
}

export default App;
