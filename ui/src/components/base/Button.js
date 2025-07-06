import React from 'react';
import { cn } from './utils';

const Button = React.forwardRef(({ 
  className, 
  variant = 'default', 
  size = 'default', 
  children, 
  ...props 
}, ref) => {
  const baseClasses = "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";
  
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    ghost: "hover:bg-gray-100 text-gray-900",
    outline: "border border-gray-200 bg-white text-gray-900 hover:bg-gray-50",
    secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
  };
  
  const sizes = {
    default: "h-9 px-4 py-2",
    sm: "h-8 px-3 py-1",
    lg: "h-12 px-6 py-3",
    icon: "h-9 w-9",
  };
  
  return (
    <button
      ref={ref}
      className={cn(
        baseClasses,
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
});

Button.displayName = "Button";

export { Button };
