import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { DarkModeProvider } from './contexts/DarkModeContext';
import { SettingsProvider } from './contexts/SettingsContext';
import SplashOverlay from './components/SplashOverlay';
import { AppLayout } from './components/layout/AppLayout';
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
      <DarkModeProvider>
        <SettingsProvider>
          <WebSocketProvider>
            <SplashOverlay 
              onGetStarted={handleGetStarted}
              isTransitioning={isTransitioning}
            />
          </WebSocketProvider>
        </SettingsProvider>
      </DarkModeProvider>
    );
  }

  return (
    <DarkModeProvider>
      <SettingsProvider>
        <WebSocketProvider>
          <Router>
            <AppWithLayout />
          </Router>
        </WebSocketProvider>
      </SettingsProvider>
    </DarkModeProvider>
  );
}

// Component to handle navigation within Router context
function AppWithLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleNavigate = (path) => {
    navigate(path);
  };

  return (
    <AppLayout currentPath={location.pathname} onNavigate={handleNavigate}>
      <Routes>
        {/* Default to Dispatch */}
        <Route index element={<DispatchPage />} />
        
        {/* Main Dispatch Command Center */}
        <Route path="dispatch" element={<DispatchPage />} />
        
        {/* Dashboard and Analytics */}
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        
        {/* Management Sections */}
        <Route path="loads" element={<LoadsPage />} />
        <Route path="fleet" element={<FleetPage />} />
        <Route path="drivers" element={<DriversPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Routes>
    </AppLayout>
  );
}

export default App;
