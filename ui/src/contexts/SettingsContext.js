import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

// Default settings configuration
const defaultSettings = {
  realTimeUpdates: true,
  notifications: true,
  language: 'en-US',
  autoRefresh: true,
  refreshInterval: 5000, // 5 seconds
  mapStyle: 'standard', // 'standard', 'satellite', 'terrain'
  compactView: false,
  soundAlerts: false,
  emailNotifications: true,
  pushNotifications: true,
  timezone: 'auto'
};

export const SettingsProvider = ({ children }) => {
  // Initialize settings from localStorage with defaults
  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('userSettings');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
    } catch (error) {
      console.error('Error loading settings from localStorage:', error);
      return defaultSettings;
    }
  });

  // Save settings to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('userSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings to localStorage:', error);
    }
  }, [settings]);

  // Update a specific setting
  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Update multiple settings at once
  const updateSettings = (newSettings) => {
    setSettings(prev => ({
      ...prev,
      ...newSettings
    }));
  };

  // Reset settings to defaults
  const resetSettings = () => {
    setSettings(defaultSettings);
    localStorage.removeItem('userSettings');
  };

  // Get a specific setting value
  const getSetting = (key) => {
    return settings[key];
  };

  // Toggle a boolean setting
  const toggleSetting = (key) => {
    updateSetting(key, !settings[key]);
  };

  const value = {
    settings,
    updateSetting,
    updateSettings,
    resetSettings,
    getSetting,
    toggleSetting,
    // Quick access to commonly used settings
    realTimeUpdates: settings.realTimeUpdates,
    notifications: settings.notifications,
    language: settings.language,
    autoRefresh: settings.autoRefresh,
    refreshInterval: settings.refreshInterval,
    mapStyle: settings.mapStyle,
    compactView: settings.compactView,
    soundAlerts: settings.soundAlerts,
    emailNotifications: settings.emailNotifications,
    pushNotifications: settings.pushNotifications,
    timezone: settings.timezone
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export default SettingsContext;
