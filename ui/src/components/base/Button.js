import React from 'react';
import { cn } from './utils';

const Button = React.forwardRef(({ 
  className, 
  variant = 'default', 
  size = 'default', 
  children, 
  ...props 
}, ref) => {
  const baseClasses = "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 outline-none focus-visible:ring-2 focus-visible:ring-primary dark:focus-visible:ring-primary focus-visible:ring-offset-2 dark:focus-visible:ring-offset-background";
  
  const variants = {
    default: "bg-primary text-background hover:bg-primary/80 dark:bg-primary dark:text-background dark:hover:bg-primary/80",
    ghost: "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-900 dark:text-foreground",
    outline: "border border-gray-200 dark:border-accent bg-white dark:bg-gray-900 text-gray-900 dark:text-foreground hover:bg-gray-50 dark:hover:bg-gray-800",
    secondary: "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-foreground hover:bg-gray-200 dark:hover:bg-gray-700",
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
