import React from 'react'
import { cn } from './cn'

export interface SegmentOption<T extends string = string> {
  value: T
  label: string
}

interface SegmentedControlProps<T extends string = string> {
  options: SegmentOption<T>[]
  value: T
  onChange: (value: T) => void
  className?: string
  size?: 'sm' | 'md'
}

export function SegmentedControl<T extends string = string>({
  options,
  value,
  onChange,
  className,
  size = 'sm',
}: SegmentedControlProps<T>) {
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center p-1 rounded-full bg-surface-2 border border-border-subtle',
        className
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.value)}
            className={cn(
              'rounded-full font-medium transition-all duration-150 whitespace-nowrap',
              size === 'sm' ? 'px-3 py-1.5 text-[12.5px]' : 'px-4 py-2 text-[13.5px]',
              active
                ? 'bg-surface-3 text-txt-primary border border-border-strong shadow-sm'
                : 'text-txt-secondary hover:text-txt-primary border border-transparent'
            )}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
