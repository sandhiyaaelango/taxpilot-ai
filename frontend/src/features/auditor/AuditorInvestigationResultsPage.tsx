import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency } from '@/utils'
import {
  FileSearch,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  FileCheck2,
  ArrowRight,
  CalendarClock,
  Layers,
} from 'lucide-react'
import {
  GlassCard,
  Button,
  StatusBadge,
  DataTable,
  EmptyState,
  SkeletonCard,
  PageHeader,
  type DataTableColumn,
} from '@/components/ui'

export function AuditorInvestigationResultsPage() {
  const [searchParams] = useSearchParams()
  const paramId = searchParams.get('id')

  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramId || '')
  const [invData, setInvData] = useState<any>(null)
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [editingDeadline, setEditingDeadline] = useState(false)
  const [newDeadline, setNewDeadline] = useState('')
  const [savingDeadline, setSavingDeadline] = useState(false)

  useEffect(() => {
    async function loadList() {
      try {
        const res = await api.get('/investigations?page_size=20')
        if (res.data.success && res.data.data.length > 0) {
          setInvestigations(res.data.data)
          if (!selectedId) setSelectedId(res.data.data[0].id)
        }
      } catch (e) {
        console.error('Failed to load investigations', e)
      }
    }
    loadList()
  }, [])

  useEffect(() => {
    if (!selectedId) return
    async function loadInvestigationDetails() {
      setLoading(true)
      try {
        const [invRes, eviRes] = await Promise.all([
          api.get(`/investigations/${selectedId}`),
          api.get(`/investigations/${selectedId}/evidence`),
        ])
        if (invRes.data.success) setInvData(invRes.data.data)
        if (eviRes.data.success) setEvidenceData(eviRes.data.data)
      } catch (e) {
        console.error('Failed to load details', e)
      } finally {
        setLoading(false)
      }
    }
    loadInvestigationDetails()
  }, [selectedId])

  const hypotheses = evidenceData?.hypotheses || []
  const supported = hypotheses.filter((h: any) => h.status === 'SUPPORTED')
  const contradicted = hypotheses.filter((h: any) => h.status === 'CONTRADICTED')
  const unverified = hypotheses.filter(
    (h: any) => h.status === 'UNVERIFIED' || h.status === 'FORMULATED'
  )
  const mismatchItems =
    invData?.workflow_state?.mismatch_results ||
    invData?.workflow_state?.mismatch_items ||
    []

  const itcClaimed = invData?.notice?.itc_claimed
  const itcAvailable = invData?.notice?.itc_available
  const varianceAmount = invData?.mismatch_amount ?? invData?.notice?.itc_mismatch

  const verificationResult = invData?.workflow_state?.verification_result
  const gatePassed =
    verificationResult?.passed ??
    ['AWAITING_APPROVAL', 'APPROVED', 'COMPLETED'].includes(invData?.status)

  const handleUpdateDeadline = async () => {
    if (!selectedId || !newDeadline) return
    setSavingDeadline(true)
    try {
      const res = await api.patch(`/investigations/${selectedId}/deadline`, {
        response_deadline: newDeadline,
      })
      if (res.data.success) {
        const refreshed = await api.get(`/investigations/${selectedId}`)
        if (refreshed.data.success) setInvData(refreshed.data.data)
        setEditingDeadline(false)
      }
    } catch (e) {
      console.error('Failed to update deadline', e)
    } finally {
      setSavingDeadline(false)
    }
  }

  const mismatchColumns: DataTableColumn<any>[] = [
    {
      key: 'id',
      header: 'Mismatch ID',
      render: (m) => (
        <span className="font-mono font-medium text-txt-primary">{m.mismatch_id}</span>
      ),
    },
    {
      key: 'invoice',
      header: 'Invoice Ref',
      render: (m) => (
        <span className="font-mono text-txt-secondary">{m.invoice_ref || '—'}</span>
      ),
    },
    {
      key: 'classification',
      header: 'Classification',
      render: (m) => (
        <span className="px-2.5 py-1 rounded-full bg-surface-3 text-[12px] text-txt-primary">
          {m.classification || 'Unclassified'}
        </span>
      ),
    },
    {
      key: 'period',
      header: 'Tax Period',
      render: (m) => (
        <span className="font-mono tabular-nums text-txt-secondary">
          {m.tax_period || '—'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (m) => <StatusBadge status={m.status || 'PENDING'} />,
    },
    {
      key: 'amount',
      header: 'Amount',
      align: 'right',
      render: (m) => (
        <span className="font-medium tabular-nums text-txt-primary">
          {formatCurrency(m.mismatch_amount)}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-5">
      <PageHeader
        title="Investigation Results"
        subtitle="Reconciliation ledger, mismatch breakdown, root-cause hypotheses, and deterministic verification."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Results' },
        ]}
        actions={
          <select
            aria-label="Select investigation"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="h-11 px-4 rounded-full bg-surface-2 border border-border-subtle text-[13.5px] font-medium text-txt-primary focus:outline-none focus:border-brand-orange/70 min-w-[240px]"
          >
            {investigations.map((i) => (
              <option key={i.id} value={i.id} className="bg-elevated text-txt-primary">
                {i.title} ({i.status})
              </option>
            ))}
          </select>
        }
      />

      {loading ? (
        <div className="space-y-5">
          <SkeletonCard className="h-40" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <SkeletonCard className="h-28" />
            <SkeletonCard className="h-28" />
            <SkeletonCard className="h-28" />
          </div>
        </div>
      ) : !invData ? (
        <EmptyState
          icon={<FileSearch className="w-5 h-5" />}
          title="No investigation selected"
          description="Select an investigation above or upload a new GST notice."
        />
      ) : (
        <div className="space-y-5">
          {/* Hero Summary */}
          <GlassCard className="relative overflow-hidden">
            <div
              aria-hidden="true"
              className="absolute -top-16 -right-12 w-64 h-64 rounded-full bg-brand-orange/15 blur-[80px] pointer-events-none"
            />
            <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2.5">
                  <StatusBadge status={invData.status} />
                  <span className="text-[13px] font-mono tabular-nums text-txt-secondary">
                    {invData.notice?.notice_number || 'Notice'} •{' '}
                    {invData.client?.primary_gstin || invData.notice?.gstin || '—'}
                  </span>
                </div>
                <h2 className="text-[22px] font-semibold text-txt-primary">
                  {invData.title}
                </h2>
                <div className="flex flex-wrap items-center gap-4 text-[13px] text-txt-secondary">
                  <span>
                    Period:{' '}
                    <strong className="font-mono tabular-nums text-txt-primary">
                      {invData.tax_period || invData.notice?.tax_period || '—'}
                    </strong>
                  </span>
                  <span>
                    Type:{' '}
                    <strong className="text-txt-primary">
                      {invData.notice?.notice_type || 'GST Notice'}
                    </strong>
                  </span>
                </div>
              </div>

              <div className="lg:text-right shrink-0">
                <div className="text-[12.5px] text-txt-muted">Total Alleged Mismatch</div>
                <div className="text-[36px] leading-[42px] font-medium tabular-nums text-txt-primary">
                  {varianceAmount != null ? formatCurrency(varianceAmount) : '—'}
                </div>
                <div className="mt-2 flex items-center lg:justify-end gap-2">
                  <CalendarClock className="w-4 h-4 text-brand-amber" />
                  {editingDeadline ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="date"
                        value={newDeadline}
                        onChange={(e) => setNewDeadline(e.target.value)}
                        className="h-8 px-2.5 rounded-lg bg-surface-2 border border-border-subtle text-[12px] font-mono text-txt-primary"
                      />
                      <Button
                        size="sm"
                        variant="primary"
                        loading={savingDeadline}
                        onClick={handleUpdateDeadline}
                      >
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingDeadline(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <>
                      <span className="text-[12.5px] text-txt-secondary font-mono tabular-nums">
                        Due:{' '}
                        {invData.response_deadline
                          ? String(invData.response_deadline).slice(0, 10)
                          : 'Not set'}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setNewDeadline(
                            invData.response_deadline
                              ? String(invData.response_deadline).slice(0, 10)
                              : ''
                          )
                          setEditingDeadline(true)
                        }}
                        className="text-[12px] text-brand-orange hover:text-brand-amber font-medium"
                      >
                        Edit
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Three Financial Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <GlassCard>
              <div className="text-[13px] text-txt-secondary">GSTR-3B ITC Claimed</div>
              <div className="text-[28px] leading-[34px] font-medium tabular-nums text-txt-primary mt-1.5">
                {itcClaimed != null ? formatCurrency(itcClaimed) : '—'}
              </div>
              <div className="text-[12px] text-txt-muted mt-1">Declared in monthly return</div>
            </GlassCard>

            <GlassCard>
              <div className="text-[13px] text-txt-secondary">GSTR-2B ITC Available</div>
              <div className="text-[28px] leading-[34px] font-medium tabular-nums text-accent-mint mt-1.5">
                {itcAvailable != null ? formatCurrency(itcAvailable) : '—'}
              </div>
              <div className="text-[12px] text-txt-muted mt-1">Auto-drafted supplier credits</div>
            </GlassCard>

            <GlassCard>
              <div className="text-[13px] text-txt-secondary">ITC Variance</div>
              <div className="text-[28px] leading-[34px] font-medium tabular-nums text-brand-orange mt-1.5">
                {varianceAmount != null ? formatCurrency(varianceAmount) : '—'}
              </div>
              <div className="text-[12px] text-txt-muted mt-1">Subject to reconciliation</div>
            </GlassCard>
          </div>

          {/* Mismatch-Level Breakdown */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary flex items-center gap-2">
                <Layers className="w-4 h-4 text-brand-orange" />
                <span>Mismatch Breakdown ({mismatchItems.length})</span>
              </h3>
            </div>
            <DataTable
              columns={mismatchColumns}
              data={mismatchItems}
              keyExtractor={(m) => String(m.mismatch_id)}
              emptyState={
                <EmptyState
                  icon={<Layers className="w-5 h-5" />}
                  description="No individual mismatch line items extracted for this investigation."
                />
              }
            />
          </GlassCard>

          {/* Root-Cause Hypotheses */}
          <GlassCard className="space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary">
                  Root-Cause Hypotheses
                </h3>
                <p className="text-[13px] text-txt-secondary mt-0.5">
                  Categorized by Evidence Challenge Engine into Supported, Contradicted, and Unverified.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusBadge status="SUPPORTED" label={`${supported.length} Supported`} />
                <StatusBadge status="CONTRADICTED" label={`${contradicted.length} Contradicted`} />
                <StatusBadge status="UNVERIFIED" label={`${unverified.length} Unverified`} />
              </div>
            </div>

            {hypotheses.length === 0 ? (
              <EmptyState
                icon={<FileSearch className="w-5 h-5" />}
                description="Root-cause hypotheses will appear after the investigation pipeline runs."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  {
                    title: 'Supported Findings',
                    icon: CheckCircle2,
                    color: 'text-accent-mint',
                    items: supported,
                    tone: 'border-accent-mint/25 bg-accent-mint/[0.04]',
                  },
                  {
                    title: 'Contradicted',
                    icon: XCircle,
                    color: 'text-danger',
                    items: contradicted,
                    tone: 'border-danger/25 bg-danger/[0.04]',
                  },
                  {
                    title: 'Unverified / Gaps',
                    icon: AlertCircle,
                    color: 'text-warning',
                    items: unverified,
                    tone: 'border-warning/25 bg-warning/[0.04]',
                  },
                ].map((col) => {
                  const Icon = col.icon
                  return (
                    <div key={col.title} className="space-y-3">
                      <div className={`flex items-center gap-2 text-[13.5px] font-medium ${col.color}`}>
                        <Icon className="w-4 h-4" />
                        <span>
                          {col.title} ({col.items.length})
                        </span>
                      </div>
                      {col.items.length === 0 ? (
                        <div className="p-4 rounded-inner bg-surface-2 text-[13px] text-txt-muted">
                          None in this category.
                        </div>
                      ) : (
                        col.items.map((h: any) => (
                          <div
                            key={h.id}
                            className={`p-4 rounded-inner border space-y-2 ${col.tone}`}
                          >
                            <div className="text-[14px] font-medium text-txt-primary">
                              {h.title}
                            </div>
                            <div className="text-[13px] leading-[19px] text-txt-secondary">
                              {h.description}
                            </div>
                            {h.challenge_rationale && (
                              <div className="p-2.5 rounded-xl bg-base/70 border border-border-subtle text-[12px] font-mono text-txt-secondary">
                                {h.challenge_rationale}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </GlassCard>

          {/* Verification Gate & Statutory References */}
          <GlassCard className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-accent-mint" />
                <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary">
                  Verification Gate &amp; Statutory Basis
                </h3>
              </div>
              <StatusBadge
                status={gatePassed ? 'SUPPORTED' : 'PENDING'}
                label={gatePassed ? 'Deterministic Gate Passed' : 'Verification Pending'}
              />
            </div>

            <div className="p-4 rounded-inner bg-surface-2 border border-border-subtle text-[13.5px] leading-[22px] text-txt-secondary">
              {verificationResult?.summary ||
                'Statutory references: Section 16(2) CGST Act, Rule 36(4) CGST Rules, and CBIC Circular 183/15/2022-GST.'}
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3 pt-2">
              <Link to={`/app/auditor/response-drafts?id=${selectedId}`}>
                <Button variant="secondary" leftIcon={<FileCheck2 className="w-4 h-4" />}>
                  Open Response Draft
                </Button>
              </Link>
              <Link to={`/app/auditor/pending-review?id=${selectedId}`}>
                <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Proceed to Approval
                </Button>
              </Link>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
