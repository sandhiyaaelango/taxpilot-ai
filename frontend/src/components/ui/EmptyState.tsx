import React from 'react'
import { cn } from './cn'

interface EmptyStateProps {
  icon: React.ReactNode
  title?: string
  description: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-10 px-6 rounded-inner bg-surface-1 border border-border-subtle',
        className
      )}
    >
      <div className="w-11 h-11 rounded-full bg-surface-2 border border-border-subtle flex items-center justify-center text-txt-secondary mb-3.5">
        {icon}
      </div>
      {title && (
        <h4 className="text-[16px] font-medium text-txt-primary mb-1">{title}</h4>
      )}
      <p className="text-[14px] text-txt-secondary max-w-sm leading-[20px]">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
