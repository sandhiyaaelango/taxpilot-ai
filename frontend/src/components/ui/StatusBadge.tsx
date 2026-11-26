import React from 'react'
import { cn } from './cn'

export type StatusTone =
  | 'pending'
  | 'running'
  | 'success'
  | 'danger'
  | 'warning'
  | 'retrying'
  | 'unverified'
  | 'info'

interface StatusConfig {
  tone: StatusTone
  label: string
}

const STATUS_MAP: Record<string, StatusConfig> = {
  PENDING: { tone: 'pending', label: 'Pending' },
  PARSED: { tone: 'info', label: 'Parsed' },
  VALIDATED: { tone: 'success', label: 'Validated' },
  PARSING_NOTICE: { tone: 'running', label: 'Parsing Notice' },
  VALIDATING_NOTICE: { tone: 'running', label: 'Validating Notice' },
  BUILDING_PLAN: { tone: 'running', label: 'Building Plan' },
  INVESTIGATING: { tone: 'running', label: 'Investigating' },
  CHALLENGING_EVIDENCE: { tone: 'running', label: 'Challenging Evidence' },
  VERIFYING: { tone: 'running', label: 'Verifying' },
  DRAFTING_RESPONSE: { tone: 'running', label: 'Drafting Response' },
  RUNNING: { tone: 'running', label: 'Running' },
  IN_PROGRESS: { tone: 'running', label: 'In Progress' },
  COMPLETED: { tone: 'success', label: 'Completed' },
  SUPPORTED: { tone: 'success', label: 'Supported' },
  APPROVED: { tone: 'success', label: 'Approved' },
  ACTIVE: { tone: 'success', label: 'Active' },
  FILED: { tone: 'success', label: 'Filed' },
  CONNECTED: { tone: 'success', label: 'Connected' },
  HEALTHY: { tone: 'success', label: 'Healthy' },
  FAILED: { tone: 'danger', label: 'Failed' },
  CONTRADICTED: { tone: 'danger', label: 'Contradicted' },
  REJECTED: { tone: 'danger', label: 'Rejected' },
  NOT_FILED: { tone: 'danger', label: 'Not Filed' },
  INACTIVE: { tone: 'danger', label: 'Inactive' },
  ERROR: { tone: 'danger', label: 'Error' },
  BLOCKED: { tone: 'warning', label: 'Blocked' },
  NEEDS_MORE_EVIDENCE: { tone: 'warning', label: 'Needs Evidence' },
  AWAITING_APPROVAL: { tone: 'retrying', label: 'Awaiting Approval' },
  RETRYING: { tone: 'retrying', label: 'Retrying' },
  UNVERIFIED: { tone: 'unverified', label: 'Unverified' },
  AUDITOR: { tone: 'success', label: 'Auditor' },
  ADMIN: { tone: 'running', label: 'Admin' },
  OWNER: { tone: 'running', label: 'Admin' },
}

const TONE_STYLES: Record<StatusTone, { pill: string; dot: string }> = {
  pending: {
    pill: 'bg-white/10 text-txt-secondary border border-border-subtle',
    dot: 'bg-txt-secondary',
  },
  running: {
    pill: 'bg-brand-orange/12 text-brand-orange border border-brand-orange/25',
    dot: 'bg-brand-orange animate-pulse',
  },
  success: {
    pill: 'bg-accent-mint/12 text-accent-mint border border-accent-mint/25',
    dot: 'bg-accent-mint',
  },
  danger: {
    pill: 'bg-danger/12 text-danger border border-danger/25',
    dot: 'bg-danger',
  },
  warning: {
    pill: 'bg-warning/12 text-warning border border-warning/25',
    dot: 'bg-warning',
  },
  retrying: {
    pill: 'bg-brand-amber/12 text-brand-amber border border-brand-amber/25',
    dot: 'bg-brand-amber',
  },
  unverified: {
    pill: 'bg-transparent text-warning border border-warning/50',
    dot: 'bg-warning',
  },
  info: {
    pill: 'bg-info/12 text-info border border-info/25',
    dot: 'bg-info',
  },
}

interface StatusBadgeProps {
  status: string
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const key = (status || 'PENDING').toUpperCase()
  const config = STATUS_MAP[key] || {
    tone: 'pending' as StatusTone,
    label: status ? status.replace(/_/g, ' ') : 'Pending',
  }
  const styles = TONE_STYLES[config.tone]

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1 rounded-full text-[12.5px] font-medium leading-[16px] whitespace-nowrap',
        styles.pill,
        className
      )}
    >
      <span className={cn('w-2 h-2 rounded-full shrink-0', styles.dot)} aria-hidden="true" />
      <span>{label || config.label}</span>
    </span>
  )
}
