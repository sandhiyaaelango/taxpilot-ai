import React from 'react'
import { cn } from './cn'

export type ButtonVariant = 'primary' | 'secondary' | 'white' | 'ghost' | 'destructive'
export type ButtonSize = 'sm' | 'md' | 'lg'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  /** Convenience alias — icon placed on the left by default */
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  /** @deprecated Use icon instead */
  leftIcon?: React.ReactNode
  /** @deprecated Use icon + iconPosition="right" instead */
  rightIcon?: React.ReactNode
  fullWidth?: boolean
  /** Polymorphic support — pass e.g. Link component */
  as?: React.ElementType
  to?: string
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled,
      icon,
      iconPosition = 'left',
      leftIcon,
      rightIcon,
      children,
      className,
      type = 'button',
      fullWidth,
      as: Component,
      to,
      ...props
    },
    ref
  ) => {
    const variants: Record<ButtonVariant, string> = {
      primary:
        'bg-brand-orange text-white hover:bg-brand-amber hover:shadow-orange-glow active:scale-[0.99]',
      secondary:
        'bg-surface-2 text-white border border-white/10 hover:bg-surface-3 hover:border-white/20',
      white:
        'bg-white text-[#0F0703] hover:bg-white/90 shadow-sm font-semibold',
      ghost:
        'bg-transparent text-text-secondary hover:text-white hover:bg-surface-2',
      destructive:
        'bg-transparent text-status-error border border-status-error/40 hover:bg-status-error/12 hover:border-status-error/70',
    }

    const sizes: Record<ButtonSize, string> = {
      sm: 'h-9 px-3.5 text-[13px]',
      md: 'h-[44px] px-5 text-[14px]',
      lg: 'h-12 px-6 text-[15px]',
    }

    const isDisabled = disabled || loading

    const resolvedLeftIcon = iconPosition === 'left' ? (icon || leftIcon) : leftIcon
    const resolvedRightIcon = iconPosition === 'right' ? (icon || rightIcon) : rightIcon

    const baseClassName = cn(
      'inline-flex items-center justify-center gap-2 rounded-full font-medium leading-[20px]',
      'transition-all duration-150 ease-out whitespace-nowrap',
      'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none',
      variants[variant],
      sizes[size],
      fullWidth && 'w-full',
      className
    )

    const content = (
      <>
        {loading ? (
          <span
            className={cn(
              'w-4 h-4 border-2 border-t-transparent rounded-full animate-spin',
              variant === 'white' ? 'border-[#0F0703]' : 'border-current'
            )}
            aria-hidden="true"
          />
        ) : (
          resolvedLeftIcon
        )}
        <span>{children}</span>
        {!loading && resolvedRightIcon}
      </>
    )

    // Polymorphic: render as Link or any other component
    if (Component) {
      return (
        <Component
          ref={ref as any}
          to={to}
          className={baseClassName}
          {...props}
        >
          {content}
        </Component>
      )
    }

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        className={baseClassName}
        {...props}
      >
        {content}
      </button>
    )
  }
)

Button.displayName = 'Button'
