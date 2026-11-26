import React from 'react'
import { Breadcrumbs, type BreadcrumbItem } from './Breadcrumbs'
import { GlassCard } from './GlassCard'
import { cn } from './cn'

interface PageHeaderProps {
  title: string
  subtitle?: string
  description?: string
  breadcrumbs?: BreadcrumbItem[]
  actions?: React.ReactNode
  className?: string
  badge?: {
    icon?: React.ReactNode
    label: string
  }
}

export function PageHeader({
  title,
  subtitle,
  description,
  breadcrumbs,
  actions,
  className,
  badge,
}: PageHeaderProps) {
  return (
    <GlassCard className={cn('p-6 relative overflow-hidden', className)}>
      {/* Orange top accent */}
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent" />
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          {breadcrumbs && breadcrumbs.length > 0 && (
            <Breadcrumbs items={breadcrumbs} className="mb-1.5" />
          )}
          {badge && (
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-brand-orange/15 border border-brand-orange/30 text-[11px] font-semibold text-brand-amber mb-2">
              {badge.icon && <span className="text-brand-orange">{badge.icon}</span>}
              {badge.label}
            </div>
          )}
          <h1 className="font-outfit text-2xl sm:text-3xl font-semibold text-white tracking-tight">
            {title}
          </h1>
          {(subtitle || description) && (
            <p className="text-xs text-text-muted max-w-2xl">
              {subtitle || description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            {actions}
          </div>
        )}
      </div>
    </GlassCard>
  )
}
