// ui/src/App.js

import React, { useState, useEffect } from 'react';
import SplashOverlay from './components/SplashOverlay';
import DispatchMapView from './components/DispatchMapView';
import TMSDashboard from './components/TMSDashboard';
import { WebSocketProvider } from './contexts/WebSocketContext';


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
      <div className={`relative min-h-screen w-full ${isTransitioning ? 'pointer-events-none' : ''} ${appState === 'splash' ? 'bg-[#0f172a]' : appState === 'dispatch' ? 'bg-[#0f172a] overflow-auto' : 'bg-[#f8fafc] overflow-auto'}`}>
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
          <div className="min-h-screen bg-slate-50">
            <div className="bg-white shadow-sm border-b border-slate-200 p-6">
              <button 
                className="bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 mb-4 flex items-center gap-2"
                onClick={handleBackToDispatch}
              >
                ← Back to Dispatch View
              </button>
              <div className="">
                <h1 className="text-3xl font-bold text-slate-900 mb-2">TMS Management Console</h1>
                <p className="text-slate-600">Comprehensive fleet and logistics management interface</p>
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
