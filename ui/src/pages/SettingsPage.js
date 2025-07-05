import React from 'react';

const SettingsPage = () => {
    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">⚙️ Settings</h1>
                <p className="text-gray-600">Configure your system preferences and account settings</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* System Settings */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">System Configuration</h2>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <div className="font-semibold text-gray-800">Real-time Updates</div>
                                <div className="text-sm text-gray-600">Enable live data synchronization</div>
                            </div>
                            <div className="w-12 h-6 bg-green-500 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full"></div>
                            </div>
                        </div>
                        
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <div className="font-semibold text-gray-800">Notifications</div>
                                <div className="text-sm text-gray-600">Push notifications for critical events</div>
                            </div>
                            <div className="w-12 h-6 bg-green-500 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full"></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* User Preferences */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-xl font-bold text-gray-900 mb-4">User Preferences</h2>
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="font-semibold text-gray-800 mb-2">Theme</div>
                            <select className="w-full p-2 border border-gray-300 rounded-lg">
                                <option>Professional (Default)</option>
                                <option>Dark Mode</option>
                                <option>High Contrast</option>
                            </select>
                        </div>
                        
                        <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="font-semibold text-gray-800 mb-2">Language</div>
                            <select className="w-full p-2 border border-gray-300 rounded-lg">
                                <option>English (US)</option>
                                <option>Spanish</option>
                                <option>French</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
