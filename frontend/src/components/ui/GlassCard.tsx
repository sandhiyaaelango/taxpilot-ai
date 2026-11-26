import React from 'react'
import { cn } from './cn'

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg'
  elevated?: boolean
}

export function GlassCard({
  children,
  className,
  padding = 'md',
  elevated = false,
  ...props
}: GlassCardProps) {
  const padMap = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-7',
  }

  return (
    <div
      className={cn(
        'rounded-card border border-border-subtle shadow-glass backdrop-blur-md transition-colors duration-200',
        elevated ? 'bg-elevated/95' : 'bg-surface-1',
        padMap[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

interface HeroCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  description: string
  action?: React.ReactNode
}

export function HeroCard({
  title,
  description,
  action,
  className,
  children,
  ...props
}: HeroCardProps) {
  return (
    <div
      className={cn(
        'hero-card p-6 flex flex-col justify-between relative overflow-hidden',
        className
      )}
      {...props}
    >
      <div className="relative z-10 space-y-2.5">
        <h3 className="text-[22px] leading-[28px] font-semibold text-white tracking-tight">
          {title}
        </h3>
        <p className="text-[14px] leading-[20px] text-white/80 line-clamp-2">
          {description}
        </p>
      </div>
      {children && <div className="relative z-10 my-4">{children}</div>}
      {action && <div className="relative z-10 mt-5">{action}</div>}
    </div>
  )
}
