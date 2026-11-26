import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from './cn'

export interface FilterOption {
  value: string
  label: string
}

interface FilterDropdownProps {
  label?: string
  options: FilterOption[]
  value: string
  onChange: (value: string) => void
  className?: string
}

export function FilterDropdown({
  label,
  options,
  value,
  onChange,
  className,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selected = options.find((o) => o.value === value) || options[0]

  return (
    <div ref={ref} className={cn('relative inline-block', className)}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        aria-expanded={open}
        className="inline-flex items-center gap-2 h-9 px-3.5 rounded-full bg-surface-2 border border-border-subtle hover:bg-surface-3 hover:border-border-strong text-[13px] font-medium text-txt-primary transition-colors"
      >
        {label && <span className="text-txt-muted">{label}:</span>}
        <span>{selected?.label || value}</span>
        <ChevronDown className={cn('w-3.5 h-3.5 text-txt-secondary transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 mt-2 min-w-[180px] rounded-inner bg-elevated border border-border-strong p-1.5 shadow-2xl z-40"
        >
          {options.map((opt) => {
            const isSelected = opt.value === value
            return (
              <button
                key={opt.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  onChange(opt.value)
                  setOpen(false)
                }}
                className={cn(
                  'w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl text-[13px] transition-colors text-left',
                  isSelected
                    ? 'bg-surface-3 text-txt-primary font-medium'
                    : 'text-txt-secondary hover:bg-surface-2 hover:text-txt-primary'
                )}
              >
                <span>{opt.label}</span>
                {isSelected && <Check className="w-3.5 h-3.5 text-accent-mint" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
