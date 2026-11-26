export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null || Number.isNaN(Number(amount))) return '₹ 0.00'
  const formatted = new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(amount))
  return `₹ ${formatted}`
}

export function formatCompactCurrency(amount: number | null | undefined): string {
  if (amount == null || Number.isNaN(Number(amount))) return '₹ 0'
  const num = Number(amount)
  if (Math.abs(num) >= 10000000) return `₹ ${(num / 10000000).toFixed(2)} Cr`
  if (Math.abs(num) >= 100000) return `₹ ${(num / 100000).toFixed(2)} L`
  if (Math.abs(num) >= 1000) return `₹ ${(num / 1000).toFixed(1)}k`
  return `₹ ${num.toFixed(0)}`
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateString
  }
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return dateString
  }
}

/**
 * Legacy helper preserved for backward compatibility across un-migrated pages.
 * New pages should use <StatusBadge status={...} /> directly.
 */
export function getStatusBadgeClass(status: string): string {
  switch (status?.toUpperCase()) {
    case 'SUPPORTED':
    case 'APPROVED':
    case 'COMPLETED':
    case 'FILED':
    case 'ACTIVE':
    case 'VALIDATED':
      return 'bg-accent-mint/12 text-accent-mint border border-accent-mint/25'
    case 'RUNNING':
    case 'INVESTIGATING':
    case 'CHALLENGING_EVIDENCE':
    case 'VERIFYING':
    case 'DRAFTING_RESPONSE':
    case 'BUILDING_PLAN':
    case 'PARSING_NOTICE':
    case 'VALIDATING_NOTICE':
      return 'bg-brand-orange/12 text-brand-orange border border-brand-orange/30'
    case 'RETRYING':
    case 'AWAITING_APPROVAL':
    case 'PARSED':
      return 'bg-brand-amber/12 text-brand-amber border border-brand-amber/30'
    case 'UNVERIFIED':
    case 'BLOCKED':
    case 'NEEDS_MORE_EVIDENCE':
      return 'bg-warning/12 text-warning border border-warning/35'
    case 'CONTRADICTED':
    case 'REJECTED':
    case 'FAILED':
    case 'NOT_FILED':
      return 'bg-danger/12 text-danger border border-danger/30'
    default:
      return 'bg-surface-2 text-txt-secondary border border-border-subtle'
  }
}
