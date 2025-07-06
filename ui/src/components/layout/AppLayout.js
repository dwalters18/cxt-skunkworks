import React, { useState } from 'react';
import { cn } from '../base/utils';
import { Button } from '../base/Button';
import { 
  Search, 
  Home, 
  Package, 
  Users, 
  Truck, 
  Route, 
  BarChart3, 
  Activity, 
  Settings,
  Menu,
  Bell,
  MapPin,
  X
} from 'lucide-react';

const navigationItems = [
  { id: 'dispatch', label: 'Dispatch Board', icon: MapPin, path: '/' },
  { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/dashboard' },
  { id: 'loads', label: 'Loads', icon: Package, path: '/loads' },
  { id: 'drivers', label: 'Drivers', icon: Users, path: '/drivers' },
  { id: 'fleet', label: 'Fleet', icon: Truck, path: '/fleet' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/analytics' },
  { id: 'events', label: 'Events', icon: Activity, path: '/events' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

export function AppLayout({ children, currentPath, onNavigate }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Determine current page from path
  const getCurrentPage = () => {
    const currentItem = navigationItems.find(item => item.path === currentPath);
    return currentItem ? currentItem.id : 'dispatch';
  };
  
  const currentPage = getCurrentPage();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 lg:block hidden">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 p-6 border-b border-gray-200">
            <img src="/images/operations-logo.svg" alt="Operations Logo" className="w-8 h-8" />
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <Button
                  key={item.id}
                  variant={isActive ? "default" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 h-12",
                    isActive && "bg-blue-600 text-white hover:bg-blue-700"
                  )}
                  onClick={() => onNavigate(item.path)}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Button>
              );
            })}
          </nav>

          {/* Status */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">System Online</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-white border-r border-gray-200">
            <div className="flex flex-col h-full">
              {/* Logo */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <img src="/images/operations-logo.svg" alt="Operations Logo" className="w-8 h-8" />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSidebarOpen(false)}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>

              {/* Navigation */}
              <nav className="flex-1 p-4 space-y-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentPage === item.id;
                  return (
                    <Button
                      key={item.id}
                      variant={isActive ? "default" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 h-12",
                        isActive && "bg-blue-600 text-white hover:bg-blue-700"
                      )}
                      onClick={() => {
                        onNavigate(item.path);
                        setSidebarOpen(false);
                      }}
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                    </Button>
                  );
                })}
              </nav>

              {/* Status */}
              <div className="p-4 border-t border-gray-200">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-600">System Online</span>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </Button>

            {/* Search */}
            <div className="flex-1 max-w-lg mx-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search loads, drivers, vehicles..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon">
                <Bell className="w-5 h-5" />
              </Button>
              
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">AD</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
