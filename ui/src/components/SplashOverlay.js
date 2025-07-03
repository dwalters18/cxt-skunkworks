import React from 'react';
import './SplashOverlay.css';

const SplashOverlay = ({ onGetStarted }) => {
    return (
        <div className="splash-overlay">
            {/* Blurred Dark Map Background */}
            <div className="splash-background">
                <div className="map-blur-layer"></div>
            </div>
            
            {/* Modal Content */}
            <div className="splash-modal">
                <div className="splash-content">
                    <h1 className="splash-title">
                        The Next Generation of Logistics & Courier Software
                    </h1>
                    <h4 className="splash-subtitle">
                        AI-powered. Autonomous. Built for the future of delivery.
                    </h4>
                    <p className="splash-description">
                        Intelligent last-mile, route, and on-demand shipment orchestration that adapts and scales with your operation—empowering drivers, dispatchers, and clients with precision, speed, and ease.
                    </p>
                    
                    <button className="get-started-btn" onClick={onGetStarted}>
                        <span className="btn-text">Get Started</span>
                        <span className="btn-glow"></span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SplashOverlay;