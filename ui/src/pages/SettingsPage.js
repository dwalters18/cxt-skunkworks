import React from 'react';
import { useDarkMode } from '../contexts/DarkModeContext';
import { useSettings } from '../contexts/SettingsContext';

const SettingsPage = () => {
    const { isDarkMode, toggleDarkMode } = useDarkMode();
    const { 
        realTimeUpdates, 
        notifications, 
        language, 
        autoRefresh,
        soundAlerts,
        emailNotifications,
        pushNotifications,
        toggleSetting, 
        updateSetting 
    } = useSettings();
    
    // Toggle component for reusability
    const ToggleSwitch = ({ checked, onChange, disabled = false }) => (
        <button
            onClick={onChange}
            disabled={disabled}
            className={`relative inline-flex h-6 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                checked ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-600'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            role="switch"
            aria-checked={checked}
        >
            <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    checked ? 'translate-x-6' : 'translate-x-0'
                }`}
            />
        </button>
    );
    
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-foreground">Settings</h1>
                <p className="text-gray-600 dark:text-muted mt-1">Configure your system preferences and account settings</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* System Settings */}
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">System Configuration</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">Real-time Updates</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Enable live data synchronization</div>
                            </div>
                            <ToggleSwitch 
                                checked={realTimeUpdates} 
                                onChange={() => toggleSetting('realTimeUpdates')}
                            />
                        </div>
                        
                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">Auto Refresh</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Automatically refresh data every 5 seconds</div>
                            </div>
                            <ToggleSwitch 
                                checked={autoRefresh} 
                                onChange={() => toggleSetting('autoRefresh')}
                            />
                        </div>

                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">Sound Alerts</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Play sounds for important notifications</div>
                            </div>
                            <ToggleSwitch 
                                checked={soundAlerts} 
                                onChange={() => toggleSetting('soundAlerts')}
                            />
                        </div>
                    </div>
                </div>

                {/* User Preferences */}
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">User Preferences</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="font-medium text-gray-900 dark:text-foreground mb-2">Theme</div>
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium text-gray-900 dark:text-foreground">Dark Mode</div>
                                    <div className="text-sm text-gray-600 dark:text-muted">Switch between light and dark themes</div>
                                </div>
                                <ToggleSwitch 
                                    checked={isDarkMode} 
                                    onChange={toggleDarkMode}
                                />
                            </div>
                        </div>
                        
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="font-semibold text-gray-800 dark:text-foreground mb-2">Language</div>
                            <select 
                                value={language}
                                onChange={(e) => updateSetting('language', e.target.value)}
                                className="w-full p-2 border border-gray-300 dark:border-accent rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-foreground focus:ring-2 focus:ring-primary"
                            >
                                <option value="en-US">English (US)</option>
                                <option value="es-ES">Spanish</option>
                                <option value="fr-FR">French</option>
                                <option value="de-DE">German</option>
                                <option value="it-IT">Italian</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Notification Settings */}
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z"/>
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7H4l5-5v5z"/>
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7h5v5"/>
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17H4v-5"/>
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">Notifications</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">Push Notifications</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Browser push notifications for critical events</div>
                            </div>
                            <ToggleSwitch 
                                checked={pushNotifications} 
                                onChange={() => toggleSetting('pushNotifications')}
                            />
                        </div>
                        
                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">Email Notifications</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Send notifications via email</div>
                            </div>
                            <ToggleSwitch 
                                checked={emailNotifications} 
                                onChange={() => toggleSetting('emailNotifications')}
                            />
                        </div>

                        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div>
                                <div className="font-medium text-gray-900 dark:text-foreground">General Notifications</div>
                                <div className="text-sm text-gray-600 dark:text-muted">Enable all notification types</div>
                            </div>
                            <ToggleSwitch 
                                checked={notifications} 
                                onChange={() => toggleSetting('notifications')}
                            />
                        </div>
                    </div>
                </div>

                {/* Data & Performance */}
                <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-accent p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
                            <svg className="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                        </div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-foreground">Data & Performance</h2>
                    </div>
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="font-medium text-gray-900 dark:text-foreground mb-2">Settings Status</div>
                            <div className="text-sm space-y-1">
                                <div className="flex justify-between">
                                    <span className="text-gray-600 dark:text-muted">Auto Refresh:</span>
                                    <span className={autoRefresh ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                                        {autoRefresh ? 'Enabled' : 'Disabled'}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600 dark:text-muted">Real-time Updates:</span>
                                    <span className={realTimeUpdates ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                                        {realTimeUpdates ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600 dark:text-muted">Language:</span>
                                    <span className="text-gray-900 dark:text-foreground">{language}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
