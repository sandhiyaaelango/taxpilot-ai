import React, { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from './cn'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightElement?: React.ReactNode
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, leftIcon, rightElement, type = 'text', className, id, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false)
    const isPassword = type === 'password'
    const resolvedType = isPassword ? (showPassword ? 'text' : 'password') : type

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={id}
            className="block text-[13px] font-medium text-txt-secondary mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-txt-muted">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={id}
            type={resolvedType}
            aria-invalid={error ? 'true' : undefined}
            className={cn(
              'w-full h-[48px] rounded-inner bg-surface-2 border text-[15px] text-txt-primary placeholder:text-txt-muted transition-all duration-150 ease-out focus:outline-none',
              leftIcon ? 'pl-11' : 'pl-4',
              isPassword || rightElement ? 'pr-11' : 'pr-4',
              error
                ? 'border-danger/70 focus:ring-2 focus:ring-danger/40'
                : 'border-border-subtle focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40',
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-full text-txt-muted hover:text-txt-primary hover:bg-surface-3 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
          {!isPassword && rightElement && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {rightElement}
            </div>
          )}
        </div>
        {error && (
          <p role="alert" className="mt-1.5 text-[12.5px] text-danger">
            {error}
          </p>
        )}
        {!error && hint && (
          <p className="mt-1.5 text-[12.5px] text-txt-muted">{hint}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'
