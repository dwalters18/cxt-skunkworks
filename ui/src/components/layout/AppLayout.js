import React from 'react';
import { Outlet } from 'react-router-dom';
import NavigationBar from '../navigation/NavigationBar';

const AppLayout = () => {
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Navigation Bar */}
            <NavigationBar />
            
            {/* Main Content Area */}
            <main className="flex-1">
                <Outlet />
            </main>
            
            {/* Status Bar */}
            <div className="bg-blue-800 text-white px-8 py-2 text-sm flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <span className="animate-pulse text-green-400">🟢</span>
                    <span>System Online</span>
                    <span className="text-blue-300">|</span>
                    <span>Real-time Updates Active</span>
                </div>
                <div className="flex items-center gap-4">
                    <span>CXT Transport Management System</span>
                    <span className="text-yellow-300">v1.0</span>
                </div>
            </div>
        </div>
    );
};

export default AppLayout;
