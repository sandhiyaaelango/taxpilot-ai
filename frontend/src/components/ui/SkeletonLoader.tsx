import React from 'react'
import { cn } from './cn'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-inner bg-surface-2',
        className
      )}
    />
  )
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div className={cn('glass-card p-6 space-y-4', className)}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-36 rounded-full" />
        <Skeleton className="h-7 w-20 rounded-full" />
      </div>
      <Skeleton className="h-10 w-44 rounded-inner" />
      <Skeleton className="h-32 w-full rounded-inner" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="flex items-center justify-between gap-4 p-4 rounded-inner bg-surface-2">
      <div className="flex items-center gap-3.5">
        <Skeleton className="w-10 h-10 rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-40 rounded-full" />
          <Skeleton className="h-3 w-24 rounded-full" />
        </div>
      </div>
      <Skeleton className="h-4 w-24 rounded-full" />
    </div>
  )
}

/** Convenience wrapper — type="card" renders a SkeletonCard, type="row" renders SkeletonRows */
interface SkeletonLoaderProps {
  type?: 'card' | 'row'
  count?: number
  className?: string
}

export function SkeletonLoader({ type = 'row', count = 3, className }: SkeletonLoaderProps) {
  if (type === 'card') {
    return (
      <div className={cn('space-y-4', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonRow key={i} />
      ))}
    </div>
  )
}
