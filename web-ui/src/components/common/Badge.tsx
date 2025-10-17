import React from 'react';
import { cn } from '@/lib/utils';
import type { VulnerabilitySeverity, HTTPMethod } from '@/types';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', children, ...props }, ref) => {
    const baseStyles = 'badge';

    const variantStyles = {
      default: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-700 dark:text-gray-300',
      primary: 'bg-blue-100 text-blue-700 border-blue-300',
      secondary: 'bg-purple-100 text-purple-700 border-purple-300',
      success: 'bg-green-100 text-green-700 border-green-300',
      danger: 'bg-red-100 text-red-700 border-red-300',
      warning: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      info: 'bg-cyan-100 text-cyan-700 border-cyan-300'
    };

    const sizeStyles = {
      sm: 'text-xs px-2 py-0.5',
      md: 'text-sm px-2.5 py-0.5',
      lg: 'text-base px-3 py-1'
    };

    return (
      <span
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export interface SeverityBadgeProps {
  severity: VulnerabilitySeverity;
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, className }) => {
  const severityConfig = {
    critical: { label: 'Critical', variant: 'danger' as const, icon: '🔴' },
    high: { label: 'High', variant: 'warning' as const, icon: '🟠' },
    medium: { label: 'Medium', variant: 'warning' as const, icon: '🟡' },
    low: { label: 'Low', variant: 'info' as const, icon: '🔵' },
    info: { label: 'Info', variant: 'default' as const, icon: '⚪' }
  };

  const config = severityConfig[severity];

  return (
    <Badge variant={config.variant} className={className}>
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </Badge>
  );
};

export interface MethodBadgeProps {
  method: HTTPMethod;
  className?: string;
}

export const MethodBadge: React.FC<MethodBadgeProps> = ({ method, className }) => {
  const methodConfig = {
    GET: { variant: 'success' as const },
    POST: { variant: 'primary' as const },
    PUT: { variant: 'warning' as const },
    DELETE: { variant: 'danger' as const },
    PATCH: { variant: 'secondary' as const },
    HEAD: { variant: 'default' as const },
    OPTIONS: { variant: 'default' as const }
  };

  const config = methodConfig[method];

  return (
    <Badge variant={config.variant} className={cn('font-mono font-bold', className)}>
      {method}
    </Badge>
  );
};

export interface StatusBadgeProps {
  status: 'completed' | 'running' | 'failed';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const statusConfig = {
    completed: { label: '완료', variant: 'success' as const, icon: '✓' },
    running: { label: '실행 중', variant: 'info' as const, icon: '⟳' },
    failed: { label: '실패', variant: 'danger' as const, icon: '✗' }
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} className={className}>
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </Badge>
  );
};
