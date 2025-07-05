import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const NavigationBar = () => {
    const location = useLocation();
    const [showManagementDropdown, setShowManagementDropdown] = useState(false);
    const [isHovering, setIsHovering] = useState(false);
    const dropdownRef = useRef(null);
    const timeoutRef = useRef(null);

    const isActive = (path) => location.pathname === path;

    // Enhanced dropdown behavior
    const handleMouseEnter = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        setIsHovering(true);
        setShowManagementDropdown(true);
    };

    const handleMouseLeave = () => {
        setIsHovering(false);
        // Delay closing to allow moving to dropdown
        timeoutRef.current = setTimeout(() => {
            if (!isHovering) {
                setShowManagementDropdown(false);
            }
        }, 200);
    };

    const handleClick = () => {
        setShowManagementDropdown(!showManagementDropdown);
    };

    const handleDropdownMouseEnter = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        setIsHovering(true);
    };

    const handleDropdownMouseLeave = () => {
        setIsHovering(false);
        timeoutRef.current = setTimeout(() => {
            setShowManagementDropdown(false);
        }, 200);
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setShowManagementDropdown(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const mainNavItems = [
        { path: '/', label: 'Dispatch Command', icon: '🎯', primary: true },
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/analytics', label: 'Analytics', icon: '📈' },
    ];

    const managementItems = [
        { path: '/loads', label: 'Load Management', icon: '📦' },
        { path: '/fleet', label: 'Fleet Management', icon: '🚛' },
        { path: '/drivers', label: 'Driver Management', icon: '👥' },
        { path: '/settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <nav className="flex items-center justify-between bg-gradient-to-r from-blue-800 to-blue-600 shadow-lg px-8 h-16 sticky top-0 z-50 border-b-2 border-blue-400">
            {/* Brand Section */}
            <div className="flex items-center">
                <Link to="/" className="flex items-center text-white font-bold text-xl hover:scale-105 transition-transform duration-200 no-underline">
                    <span className="text-2xl mr-2 animate-pulse">🚛</span>
                    <span className="bg-gradient-to-r from-white to-yellow-300 bg-clip-text text-transparent">
                        CXT Dispatch
                    </span>
                </Link>
            </div>

            {/* Navigation Items */}
            <div className="flex items-center gap-4">
                {mainNavItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-300 no-underline relative overflow-hidden ${
                            isActive(item.path)
                                ? 'bg-white/20 text-white border-2 border-yellow-400 shadow-lg shadow-yellow-400/30'
                                : 'text-white/80 hover:text-white hover:bg-white/10 hover:-translate-y-1 hover:shadow-lg border-2 border-transparent'
                        } ${
                            item.primary
                                ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-blue-800 font-bold hover:from-yellow-500 hover:to-yellow-400 hover:scale-105 animate-pulse'
                                : ''
                        }`}
                    >
                        <span className="text-xl">{item.icon}</span>
                        <span className="text-sm whitespace-nowrap">{item.label}</span>
                    </Link>
                ))}

                {/* Management Dropdown */}
                <div 
                    ref={dropdownRef}
                    className="relative"
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    <button 
                        onClick={handleClick}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-300 text-white/80 hover:text-white hover:bg-white/10 hover:-translate-y-1 hover:shadow-lg border-2 border-transparent focus:outline-none focus:ring-2 focus:ring-white/50"
                        aria-expanded={showManagementDropdown}
                        aria-haspopup="true"
                    >
                        <span className="text-xl">⚡</span>
                        <span className="text-sm whitespace-nowrap">Management</span>
                        <span className={`text-xs transition-transform duration-300 ${showManagementDropdown ? 'rotate-180' : ''}`}>▼</span>
                    </button>

                    {showManagementDropdown && (
                        <div 
                            className="absolute top-full left-0 -mt-1 pt-3 bg-white rounded-xl shadow-xl py-2 min-w-[200px] z-50 border border-gray-200 animate-in slide-in-from-top-2 duration-300"
                            onMouseEnter={handleDropdownMouseEnter}
                            onMouseLeave={handleDropdownMouseLeave}
                        >
                            {managementItems.map((item) => (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-50 hover:text-blue-800 transition-all duration-200 font-medium no-underline hover:pl-5 ${
                                        isActive(item.path) ? 'bg-blue-50 text-blue-800 border-l-4 border-blue-600' : ''
                                    }`}
                                >
                                    <span className="text-lg">{item.icon}</span>
                                    <span className="text-sm">{item.label}</span>
                                </Link>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* User Section */}
            <div className="flex items-center">
                <div className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full text-white transition-all duration-300 hover:bg-white/20 hover:scale-105">
                    <span className="text-xl">👨‍💼</span>
                    <span className="font-semibold text-sm hidden sm:block">Dispatcher</span>
                </div>
            </div>
        </nav>
    );
};

export default NavigationBar;
