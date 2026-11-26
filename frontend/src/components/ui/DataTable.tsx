import React from 'react'
import { cn } from './cn'

export interface DataTableColumn<T> {
  key: string
  header: string
  align?: 'left' | 'right'
  className?: string
  render: (row: T) => React.ReactNode
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  onRowClick?: (row: T) => void
  emptyState?: React.ReactNode
  className?: string
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyState,
  className,
}: DataTableProps<T>) {
  if (!data.length && emptyState) {
    return <>{emptyState}</>
  }

  return (
    <div className={cn('w-full overflow-x-auto', className)}>
      <div className="min-w-[680px]">
        {/* Header row */}
        <div
          className="grid items-center gap-4 px-4 pb-3 text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted"
          style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}
        >
          {columns.map((col) => (
            <div
              key={col.key}
              className={cn(
                col.align === 'right' ? 'text-right' : 'text-left',
                col.className
              )}
            >
              {col.header}
            </div>
          ))}
        </div>

        {/* Chip rows with 8px gap */}
        <div className="flex flex-col gap-2">
          {data.map((row) => (
            <div
              key={keyExtractor(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              role={onRowClick ? 'button' : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    }
                  : undefined
              }
              className={cn(
                'grid items-center gap-4 px-4 py-3.5 rounded-inner bg-surface-2 border border-transparent transition-colors duration-150 text-[14px] leading-[20px] text-txt-primary',
                onRowClick && 'cursor-pointer hover:bg-surface-3 hover:border-border-subtle'
              )}
              style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}
            >
              {columns.map((col) => (
                <div
                  key={col.key}
                  className={cn(
                    'min-w-0',
                    col.align === 'right' ? 'text-right tabular-nums' : 'text-left',
                    col.className
                  )}
                >
                  {col.render(row)}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
