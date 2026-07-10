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
import OrdersPage from './pages/OrdersPage';
import OrderEntryPage from './pages/OrderEntryPage';
import OrderDetailPage from './pages/OrderDetailPage';
import FleetPage from './pages/FleetPage';
import DriversPage from './pages/DriversPage';
import EventsPage from './pages/EventsPage';
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
            <SplashOverlay onGetStarted={handleGetStarted} isTransitioning={isTransitioning} />
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

function AppWithLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AppLayout currentPath={location.pathname} onNavigate={navigate}>
      <Routes>
        <Route index element={<DispatchPage />} />
        <Route path="dispatch" element={<DispatchPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="orders/new" element={<OrderEntryPage />} />
        <Route path="orders/:orderId" element={<OrderDetailPage />} />
        <Route path="fleet" element={<FleetPage />} />
        <Route path="drivers" element={<DriversPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Routes>
    </AppLayout>
  );
}

export default App;
