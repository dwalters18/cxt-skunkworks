import React from 'react';

const backgroundStyle = {
  position: 'fixed',
  inset: 0,
  width: '100vw',
  height: '100vh',
  zIndex: 0,
  objectFit: 'cover',
  objectPosition: 'center',
  opacity: 0.22,
  pointerEvents: 'none',
};

const SplashOverlay = ({ onGetStarted }) => {
  return (
    <div className="fixed inset-0 bg-gradient-to-br from-logo-green to-medium-blue flex items-center justify-center">
      {/* Subtle background image for artistry */}
      <img
        src="/images/background.png"
        alt=""
        aria-hidden="true"
        style={backgroundStyle}
      />
      <div className="absolute inset-0 bg-black opacity-50"></div>
      <div className="relative z-10 bg-white bg-opacity-80 backdrop-blur-md rounded-xl p-10 max-w-md w-full text-center space-y-6">
        <h1 className="text-4xl font-heading text-logo-gray">The Next Generation of Logistics & Courier Software</h1>
        <p className="text-lg font-sans text-text-gray">AI-powered. Autonomous. Built for the future of delivery.</p>
        <p className="text-base font-sans text-text-gray">Intelligent last-mile, route, and on-demand shipment orchestration that adapts and scales with your operation—empowering drivers, dispatchers, and clients with precision, speed, and ease.</p>
        <button onClick={onGetStarted} className="mt-4 bg-logo-green hover:bg-secondary-green text-white font-bold py-3 px-6 rounded-full transition transform hover:-translate-y-1">Get Started</button>
      </div>
    </div>
  );
};

export default SplashOverlay;