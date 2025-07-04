// ui/src/App.js

import React, { useState, useEffect } from 'react';
import SplashOverlay from './components/SplashOverlay';
import DispatchMapView from './components/DispatchMapView';
import TMSDashboard from './components/TMSDashboard';
import { WebSocketProvider } from './contexts/WebSocketContext';
import './App.css';

function App() {
  const [appState, setAppState] = useState('splash'); // 'splash', 'dispatch', 'management'
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Handle scroll events to transition from dispatch to management
  useEffect(() => {
    const handleScroll = () => {
      if (appState === 'dispatch' && window.scrollY > 100) {
        transitionToManagement();
      }
    };

    if (appState === 'dispatch') {
      window.addEventListener('scroll', handleScroll);
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [appState]);

  const handleGetStarted = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setAppState('dispatch');
      setIsTransitioning(false);
    }, 800);
  };

  const transitionToManagement = () => {
    setIsTransitioning(true);
    setTimeout(() => {
      setAppState('management');
      setIsTransitioning(false);
    }, 500);
  };

  const handleBackToDispatch = () => {
    setAppState('dispatch');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <WebSocketProvider>
      <div className={`App app-state-${appState} ${isTransitioning ? 'transitioning' : ''}`}>
        {/* State 1: Splash Overlay */}
        {appState === 'splash' && (
          <SplashOverlay onGetStarted={handleGetStarted} />
        )}

        {/* State 2: Dispatch Map View */}
        {appState === 'dispatch' && (
          <DispatchMapView onTransitionToManagement={transitionToManagement} />
        )}

        {/* State 3: Management View */}
        {appState === 'management' && (
          <div className="management-view">
            <div className="management-header">
              <button className="back-to-dispatch-btn" onClick={handleBackToDispatch}>
                ← Back to Dispatch View
              </button>
              <div className="header-content">
                <h1>TMS Management Console</h1>
                <p>Comprehensive fleet and logistics management interface</p>
              </div>
            </div>
            <TMSDashboard />
          </div>
        )}

        {/* Transition Overlay */}
        {isTransitioning && <div className="transition-overlay" />}
      </div>
    </WebSocketProvider>
  );
}

export default App;
