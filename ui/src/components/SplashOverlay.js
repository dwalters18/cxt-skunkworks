import React from 'react';

const SplashOverlay = ({ onGetStarted }) => {
  return (
    <div className="relative min-h-screen flex flex-col justify-center py-12 px-8 md:px-12">
      
      {/* Full-screen background image with overlay */}
      <div 
        className="fixed inset-0 -z-10" 
        style={{
          backgroundImage: 'url("/images/background2.png")',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      />
      <div className="fixed inset-0 bg-black/50 -z-10" />
      
      {/* Header */}
      <header className="absolute font-sans top-0 left-0 right-0 z-10">
        <nav className="flex justify-between items-center w-full mx-auto max-w-7xl px-8 md:px-12 py-6">
          {/* Left Section */}
          <div className="flex items-center gap-x-8">
            {/* Nav Links */}
            <ul className="flex items-center gap-x-6">
              <li className="relative">
                <a href="#" className="text-sm text-white hover:text-primary transition-colors">
                  Home
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                  Products
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                  Services
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                  Who We Serve
                </a>
              </li>
            </ul>
          </div>
          
          {/* Right Section */}
          <ul className="flex items-center gap-x-6">
            <li>
              <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                About Us
              </a>
            </li>
            <li>
              <a href="#" className="text-sm text-gray-300 hover:text-white transition-colors">
                Careers
              </a>
            </li>
          </ul>
        </nav>
      </header>
      
      {/* Hero Content */}
      <main className="w-full max-w-7xl mx-auto">
        <div className="max-w-2xl">
          {/* Pre-headline */}
          <p className="text-xs font-sans uppercase tracking-widest text-gray-400 mb-4">
            CXT Software - An Ionic Partners Company
          </p>
          
          {/* Main Headline */}
          <h1 className="text-5xl md:text-6xl font-heading text-white leading-tight">
            The Next Generation of Logistics & Courier Software
          </h1>
          
          {/* Paragraph */}
          <p className="text-lg font-sans text-gray-300 mt-6">
            Intelligent last-mile, route, and on-demand shipment orchestration that adapts and scales with your operation—empowering drivers, dispatchers, and clients with precision, speed, and ease.
          </p>
          
          {/* Call to Action Button */}
          <button 
            onClick={onGetStarted}
            className="inline-block font-sans bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-white py-3 px-8 mt-8 hover:bg-white/20 hover:border-white/30 transition-all duration-300 shadow-lg"
          >
            Experience Now
          </button>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="absolute font-sans bottom-8 left-8 md:left-12 z-10">
        <div className="flex items-center gap-x-2">
          {/* Logo */}
          <img src="/images/logo.svg" alt="Logo" className="w-16 h-16" />
          {/* Text */}
          <p className="text-sm text-gray-500">
            25 Years of Service Excellence
          </p>
        </div>
      </footer>
    </div>
  );
};

export default SplashOverlay;