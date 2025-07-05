import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { WebSocketProvider } from './contexts/WebSocketContext';
import SplashOverlay from './components/SplashOverlay';
import AppLayout from './components/layout/AppLayout';
import DispatchPage from './pages/DispatchPage';
import DashboardPage from './pages/DashboardPage';
import AnalyticsPage from './pages/AnalyticsPage';
import LoadsPage from './pages/LoadsPage';
import FleetPage from './pages/FleetPage';
import DriversPage from './pages/DriversPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const handleGetStarted = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setShowSplash(false);
      setIsTransitioning(false);
    }, 800);
  };

  if (showSplash) {
    return (
      <WebSocketProvider>
        <SplashOverlay 
          onGetStarted={handleGetStarted}
          isTransitioning={isTransitioning}
        />
      </WebSocketProvider>
    );
  }

  return (
    <WebSocketProvider>
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            {/* Main Dispatch Command Center - Primary Focus */}
            <Route index element={<DispatchPage />} />
            
            {/* Dashboard and Analytics */}
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            
            {/* Management Sections */}
            <Route path="loads" element={<LoadsPage />} />
            <Route path="fleet" element={<FleetPage />} />
            <Route path="drivers" element={<DriversPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </Router>
    </WebSocketProvider>
  );
}

export default App;
