import React from 'react'
import { cn } from './cn'

interface AvatarProps {
  name?: string | null
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Avatar({ name, size = 'md', className }: AvatarProps) {
  const initials = (name || 'U')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() || '')
    .join('')

  const sizes = {
    sm: 'w-8 h-8 text-[12px]',
    md: 'w-9 h-9 text-[13px]',
    lg: 'w-12 h-12 text-[16px]',
  }

  return (
    <div
      className={cn(
        'rounded-full bg-surface-3 border border-border-strong text-txt-primary font-semibold flex items-center justify-center shrink-0 select-none',
        sizes[size],
        className
      )}
    >
      {initials || 'U'}
    </div>
  )
}
