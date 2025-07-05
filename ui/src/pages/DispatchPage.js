import React from 'react';
import DispatchMapView from '../components/DispatchMapView';

const DispatchPage = () => {
    return (
        <div className="h-screen flex flex-col">
            {/* Gamified Header */}
            <div className="bg-gradient-to-r from-blue-900 to-blue-700 text-white px-8 py-4 shadow-lg">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="text-3xl animate-bounce">🎯</div>
                        <div>
                            <h1 className="text-2xl font-bold">Dispatch Command Center</h1>
                            <p className="text-blue-200 text-sm">Your mission: Optimize routes and dispatch loads efficiently</p>
                        </div>
                    </div>
                    
                    {/* Gamification Stats */}
                    <div className="flex items-center gap-6">
                        <div className="text-center bg-white/10 rounded-lg px-4 py-2">
                            <div className="text-yellow-400 font-bold text-lg">🏆 85</div>
                            <div className="text-xs text-blue-200">Score Today</div>
                        </div>
                        <div className="text-center bg-white/10 rounded-lg px-4 py-2">
                            <div className="text-green-400 font-bold text-lg">⚡ 12</div>
                            <div className="text-xs text-blue-200">Routes Optimized</div>
                        </div>
                        <div className="text-center bg-white/10 rounded-lg px-4 py-2">
                            <div className="text-purple-400 font-bold text-lg">🚛 8</div>
                            <div className="text-xs text-blue-200">Active Loads</div>
                        </div>
                    </div>
                </div>
            </div>
            
            {/* Main Dispatch Map View */}
            <div className="flex-1 relative">
                <DispatchMapView />
            </div>
        </div>
    );
};

export default DispatchPage;
