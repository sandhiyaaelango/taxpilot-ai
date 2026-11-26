import React, { useEffect } from 'react'
import { X } from 'lucide-react'
import { Button } from './Button'

interface ConfirmationModalProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'primary' | 'destructive'
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
  children?: React.ReactNode
}

export function ConfirmationModal({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'primary',
  loading = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmationModalProps) {
  useEffect(() => {
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) onCancel()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [open, loading, onCancel])

  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md"
    >
      <div className="w-full max-w-md rounded-card bg-elevated border border-border-strong p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4 mb-3">
          <h3 id="confirm-modal-title" className="text-[18px] leading-[24px] font-medium text-txt-primary">
            {title}
          </h3>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            aria-label="Close modal"
            className="p-1.5 rounded-full text-txt-muted hover:text-txt-primary hover:bg-surface-2 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[14px] leading-[22px] text-txt-secondary mb-5">
          {description}
        </p>
        {children && <div className="mb-5">{children}</div>}
        <div className="flex items-center justify-end gap-3">
          <Button variant="secondary" size="md" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'destructive' ? 'destructive' : 'primary'}
            size="md"
            loading={loading}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
