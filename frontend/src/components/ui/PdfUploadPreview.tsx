import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  FileUp,
  FileCheck2,
  FileText,
  RotateCcw,
  AlertTriangle,
  Eye,
  EyeOff,
  Loader2,
} from 'lucide-react'
import { StatusBadge } from './StatusBadge'
import { cn } from './cn'

export const ALLOWED_NOTICE_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']
export const MAX_NOTICE_SIZE_BYTES = 15 * 1024 * 1024 // 15 MB (matches backend settings)

export function validateNoticeFile(file: File): string | null {
  const name = file.name.toLowerCase()
  const hasValidExt = ALLOWED_NOTICE_EXTENSIONS.some((ext) => name.endsWith(ext))
  if (!hasValidExt) {
    return `Unsupported file type. Allowed formats: PDF, PNG, JPG, JPEG.`
  }
  if (file.size === 0) {
    return 'Selected file is empty (0 bytes). Please choose a valid notice document.'
  }
  if (file.size > MAX_NOTICE_SIZE_BYTES) {
    return `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 15 MB limit.`
  }
  return null
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export type UploadStage = 'idle' | 'uploading' | 'extracting' | 'extracted' | 'error'

export interface PdfUploadPreviewProps {
  file: File | null
  onFileSelect: (file: File | null, validationError: string | null) => void
  stage: UploadStage
  uploadProgress: number
  validationStatus?: string
  warnings?: string[]
  isScanned?: boolean
  ocrRequired?: boolean
  disabled?: boolean
  className?: string
}

export function PdfUploadPreview({
  file,
  onFileSelect,
  stage,
  uploadProgress,
  validationStatus,
  warnings = [],
  isScanned,
  ocrRequired,
  disabled = false,
  className,
}: PdfUploadPreviewProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const objectUrl = useMemo(() => {
    if (!file) return null
    return URL.createObjectURL(file)
  }, [file])

  useEffect(() => {
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [objectUrl])

  const processFile = (selected: File) => {
    const err = validateNoticeFile(selected)
    if (err) {
      onFileSelect(null, err)
      return
    }
    onFileSelect(selected, null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0])
    }
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (disabled || stage === 'uploading' || stage === 'extracting') return
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0])
    }
  }

  const isBusy = stage === 'uploading' || stage === 'extracting'
  const isPdf = file?.name.toLowerCase().endsWith('.pdf')

  return (
    <div className={cn('space-y-4', className)}>
      <div
        onClick={() => !disabled && !isBusy && stage !== 'extracted' && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled && !isBusy) setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={cn(
          'rounded-inner border-2 border-dashed p-7 text-center transition-all',
          stage === 'extracted'
            ? 'border-accent-mint/40 bg-accent-mint/5 cursor-default'
            : stage === 'error'
            ? 'border-danger/45 bg-danger/5 cursor-pointer'
            : dragActive
            ? 'border-brand-orange bg-brand-orange/10 cursor-pointer'
            : isBusy
            ? 'border-brand-orange/50 bg-surface-2 cursor-wait'
            : 'border-border-strong bg-surface-2 hover:border-brand-orange/60 hover:bg-surface-3 cursor-pointer'
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled || isBusy}
        />

        <div className="w-12 h-12 rounded-full bg-surface-3 border border-border-subtle flex items-center justify-center mx-auto mb-3 text-brand-orange">
          {isBusy ? (
            <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
          ) : stage === 'extracted' ? (
            <FileCheck2 className="w-6 h-6 text-accent-mint" />
          ) : (
            <FileUp className="w-6 h-6" />
          )}
        </div>

        <div className="text-[15px] font-medium text-txt-primary break-all px-2">
          {file ? file.name : 'Drop GST Notice PDF here or click to browse'}
        </div>

        <div className="text-[13px] text-txt-secondary mt-1">
          {file ? (
            <span className="tabular-nums">
              {formatFileSize(file.size)}
              {stage === 'idle' && ' • Validated & ready for extraction'}
              {stage === 'uploading' && ` • Uploading (${uploadProgress}%)…`}
              {stage === 'extracting' && ' • Parsing notice fields with AI…'}
              {stage === 'extracted' && ' • Extraction complete'}
              {stage === 'error' && ' • Extraction failed'}
            </span>
          ) : (
            'Supports PDF, PNG, JPG, JPEG (DRC-01A, DRC-01, ASMT-10 • Max 15 MB)'
          )}
        </div>

        {/* Real Upload / Extraction Progress Bar */}
        {isBusy && (
          <div className="mt-4 max-w-xs mx-auto space-y-1.5">
            <div className="h-1.5 w-full rounded-full bg-surface-3 overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-200',
                  stage === 'extracting'
                    ? 'w-full bg-brand-amber animate-pulse'
                    : 'bg-brand-orange'
                )}
                style={stage === 'uploading' ? { width: `${Math.max(uploadProgress, 8)}%` } : undefined}
              />
            </div>
            <div className="text-[11.5px] text-txt-muted">
              {stage === 'uploading'
                ? `Sending PDF to server (${uploadProgress}%)`
                : 'Extracting text & statutory GST fields…'}
            </div>
          </div>
        )}

        {/* File action pills */}
        {file && !isBusy && (
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            {stage !== 'extracted' && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  onFileSelect(null, null)
                  setShowPreview(false)
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-3 text-[12px] text-txt-secondary hover:text-txt-primary transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Replace file</span>
              </button>
            )}
            {objectUrl && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowPreview((prev) => !prev)
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-3 text-[12px] text-brand-amber hover:text-white transition-colors"
              >
                {showPreview ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                <span>{showPreview ? 'Hide Preview' : 'Preview Document'}</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Warnings from backend extraction (e.g. scanned PDF / missing GSTIN) */}
      {(ocrRequired || isScanned || warnings.length > 0) && stage === 'extracted' && (
        <div className="p-3.5 rounded-inner bg-warning/10 border border-warning/30 space-y-1.5 text-[12.5px] text-warning">
          <div className="flex items-center justify-between gap-2 font-medium">
            <span className="flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              Extraction Notices
            </span>
            {validationStatus && <StatusBadge status={validationStatus} />}
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-txt-secondary">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Embedded Document Preview */}
      {showPreview && objectUrl && (
        <div className="rounded-inner border border-border-subtle bg-bg-elevated overflow-hidden">
          <div className="px-4 py-2.5 border-b border-border-subtle flex items-center justify-between text-[12px] text-txt-secondary">
            <span className="flex items-center gap-1.5 font-mono truncate">
              <FileText className="w-3.5 h-3.5 text-brand-orange shrink-0" />
              {file?.name}
            </span>
            <span className="text-txt-muted shrink-0">Local Preview</span>
          </div>
          {isPdf ? (
            <iframe
              src={objectUrl}
              title="Uploaded GST Notice PDF Preview"
              className="w-full h-[360px] bg-white"
            />
          ) : (
            <div className="p-4 flex justify-center bg-bg-base">
              <img
                src={objectUrl}
                alt="Uploaded GST Notice"
                className="max-h-[360px] rounded object-contain"
              />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
