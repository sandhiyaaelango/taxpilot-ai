import React from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { cn } from './cn'

export interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  if (!items.length) return null
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-1.5 text-[12.5px] text-txt-muted', className)}>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1
        return (
          <React.Fragment key={`${item.label}-${idx}`}>
            {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-txt-muted/60" />}
            {item.to && !isLast ? (
              <Link to={item.to} className="hover:text-txt-primary transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? 'text-txt-secondary font-medium' : undefined}>
                {item.label}
              </span>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
