import React from 'react';

const SettingsPage = () => {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
                <p className="text-gray-600 mt-1">Configure your system preferences and account settings</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* System Settings */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900">System Configuration</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900">Real-time Updates</div>
                                <div className="text-sm text-gray-600">Enable live data synchronization</div>
                            </div>
                            <div className="w-12 h-6 bg-green-500 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full shadow-sm"></div>
                            </div>
                        </div>
                        
                        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900">Notifications</div>
                                <div className="text-sm text-gray-600">Push notifications for critical events</div>
                            </div>
                            <div className="w-12 h-6 bg-green-500 rounded-full flex items-center justify-end px-1">
                                <div className="w-4 h-4 bg-white rounded-full shadow-sm"></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* User Preferences */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900">User Preferences</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-50 rounded-lg">
                            <div className="font-medium text-gray-900 mb-2">Theme</div>
                            <select className="w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
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
