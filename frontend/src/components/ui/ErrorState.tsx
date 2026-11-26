import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from './Button'
import { cn } from './cn'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Unable to load data',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center text-center py-10 px-6 rounded-inner bg-danger/8 border border-danger/25',
        className
      )}
    >
      <div className="w-11 h-11 rounded-full bg-danger/15 border border-danger/30 flex items-center justify-center text-danger mb-3.5">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <h4 className="text-[16px] font-medium text-txt-primary mb-1">{title}</h4>
      <p className="text-[14px] text-txt-secondary max-w-md leading-[20px]">
        {message}
      </p>
      {onRetry && (
        <div className="mt-4">
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Retry
          </Button>
        </div>
      )}
    </div>
  )
}
