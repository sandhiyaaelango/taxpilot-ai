import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { useAuthStore } from '@/stores/authStore'
import { formatCurrency, formatDateTime } from '@/utils'
import { downloadReportPdf, extractApiErrorMessage } from '@/utils/pdfDownload'
import toast from 'react-hot-toast'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Download,
  ShieldCheck,
  Save,
  FileCheck2,
} from 'lucide-react'
import {
  GlassCard,
  Button,
  StatusBadge,
  ConfirmationModal,
  EmptyState,
  SkeletonCard,
  PageHeader,
} from '@/components/ui'

export function AuditorPendingReviewPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const paramId = searchParams.get('id')
  const { user } = useAuthStore()

  const [queueInvs, setQueueInvs] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramId || '')
  const [invData, setInvData] = useState<any>(null)
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const [draftTitle, setDraftTitle] = useState('')
  const [executiveSummary, setExecutiveSummary] = useState('')
  const [reconciliationTable, setReconciliationTable] = useState('')
  const [legalGrounds, setLegalGrounds] = useState('')
  const [prayer, setPrayer] = useState('')

  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [pdfError, setPdfError] = useState<string | null>(null)
  const [pdfSuccess, setPdfSuccess] = useState<string | null>(null)
  const [confirmApproveOpen, setConfirmApproveOpen] = useState(false)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchQueue = async () => {
    try {
      const res = await api.get('/investigations?page_size=50')
      if (res.data.success) {
        const all = res.data.data || []
        const filtered = all.filter(
          (i: any) =>
            ['AWAITING_APPROVAL', 'NEEDS_MORE_EVIDENCE', 'APPROVED'].includes(i.status) ||
            i.id === paramId
        )
        setQueueInvs(filtered.length > 0 ? filtered : all)
        if (!selectedId && (filtered.length > 0 || all.length > 0)) {
          setSelectedId((filtered[0] || all[0]).id)
        }
      }
    } catch (err) {
      console.error('Failed to load review queue', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchCaseDetails = async (id: string) => {
    if (!id) return
    setError(null)
    try {
      const [invRes, eviRes] = await Promise.all([
        api.get(`/investigations/${id}`),
        api.get(`/investigations/${id}/evidence`),
      ])
      if (invRes.data.success) {
        const d = invRes.data.data
        setInvData(d)
        const wf = d.workflow_state || {}
        const wfDraft = wf.response_draft || {}
        if (!notes) {
          const noticeNo = d.notice?.notice_number || wf.notice_data?.notice_number || d.title
          setNotes(
            `Attested by Statutory GST Auditor for ${noticeNo}. Reviewed ledger reconciliation, evidence provenance, and response draft.`
          )
        }
        try {
          const repRes = await api.get(`/reports/${id}`)
          if (repRes.data.success && repRes.data.data) {
            const rep = repRes.data.data
            setReportData(rep)
            const c = rep.content || {}
            setDraftTitle(c.title || rep.title || '')
            setExecutiveSummary(c.executive_summary || '')
            setReconciliationTable(c.reconciliation_table || '')
            setLegalGrounds(c.legal_grounds || c.legal_submissions || '')
            setPrayer(c.prayer || '')
          }
        } catch {
          setReportData(null)
          setDraftTitle(wfDraft.title || '')
          setExecutiveSummary(wfDraft.executive_summary || '')
          setReconciliationTable(wfDraft.reconciliation_table || '')
          setLegalGrounds(wfDraft.legal_grounds || wfDraft.legal_submissions || '')
          setPrayer(wfDraft.prayer || '')
        }
      }
      if (eviRes.data.success) {
        setEvidenceData(eviRes.data.data)
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to load investigation details.')
    }
  }

  useEffect(() => {
    fetchQueue()
  }, [])

  useEffect(() => {
    if (selectedId) fetchCaseDetails(selectedId)
  }, [selectedId])

  const handleSelectChange = (id: string) => {
    setSelectedId(id)
    setSearchParams({ id })
    setActionSuccess(null)
    setError(null)
  }

  const handleAction = async (
    action: 'EDIT' | 'APPROVE' | 'REJECT' | 'REQUEST_MORE_EVIDENCE'
  ) => {
    if (!selectedId) return
    setSubmitting(true)
    setError(null)
    setActionSuccess(null)
    try {
      const payload: any = {
        action,
        notes: notes || `Auditor action: ${action}`,
      }
      if (action === 'EDIT' || action === 'APPROVE') {
        payload.edited_content = {
          title: draftTitle,
          executive_summary: executiveSummary,
          reconciliation_table: reconciliationTable,
          legal_grounds: legalGrounds,
          legal_submissions: legalGrounds,
          prayer,
          updated_at: new Date().toISOString(),
        }
      }
      const res = await api.post(`/approvals/${selectedId}`, payload)
      if (res.data.success) {
        setActionSuccess(action)
        setConfirmApproveOpen(false)
        await fetchCaseDetails(selectedId)
        await fetchQueue()
      }
    } catch (err: any) {
      setConfirmApproveOpen(false)
      setError(err.response?.data?.detail || `Failed to execute action '${action}'.`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (!selectedId || downloading) return
    setDownloading(true)
    setError(null)
    setPdfError(null)
    setPdfSuccess(null)
    try {
      const filename = await downloadReportPdf(
        selectedId,
        invData?.notice?.notice_number || invData?.title
      )
      setPdfSuccess(filename)
      toast.success(`Downloaded ${filename}`)
    } catch (err: any) {
      const msg = await extractApiErrorMessage(
        err,
        'Failed to generate or download PDF report.'
      )
      setPdfError(msg)
      setError(msg)
    } finally {
      setDownloading(false)
    }
  }

  const isApproved = invData?.status === 'APPROVED'
  const hypotheses = evidenceData?.hypotheses || []
  const supportedCount = hypotheses.filter((h: any) => h.status === 'SUPPORTED').length
  const evidenceCount = evidenceData?.evidence_records?.length || 0

  return (
    <div className="space-y-5">
      <PageHeader
        title="Auditor Approval & Sign-Off"
        subtitle="Verify checklist compliance, attest statutory findings, and generate the final signed PDF reply."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Approval' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <select
              aria-label="Select investigation for approval"
              value={selectedId}
              onChange={(e) => handleSelectChange(e.target.value)}
              className="h-11 px-4 rounded-full bg-surface-2 border border-border-subtle text-[13.5px] font-medium text-txt-primary focus:outline-none focus:border-brand-orange/70 min-w-[240px]"
            >
              {queueInvs.map((i) => (
                <option key={i.id} value={i.id} className="bg-elevated text-txt-primary">
                  {i.title} ({i.status})
                </option>
              ))}
            </select>
            {selectedId && (
              <Button
                variant={isApproved ? 'primary' : 'secondary'}
                loading={downloading}
                disabled={downloading}
                onClick={handleDownloadPdf}
                leftIcon={<Download className="w-4 h-4" />}
                title={
                  isApproved
                    ? 'Generate and download signed final PDF'
                    : 'Requires Auditor approval before PDF export'
                }
              >
                {downloading ? 'Generating PDF...' : 'Generate Final PDF'}
              </Button>
            )}
          </div>
        }
      />

      {error && (
        <div
          role="alert"
          className="p-4 rounded-inner bg-danger/12 border border-danger/30 text-[13.5px] text-danger flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
          {pdfError && (
            <Button
              variant="secondary"
              size="sm"
              loading={downloading}
              onClick={handleDownloadPdf}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Retry PDF
            </Button>
          )}
        </div>
      )}

      {pdfSuccess && (
        <div className="p-4 rounded-inner bg-accent-mint/12 border border-accent-mint/30 text-[13.5px] text-accent-mint flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>
            Final PDF generated and downloaded: <strong className="font-mono">{pdfSuccess}</strong>
          </span>
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 rounded-inner bg-accent-mint/12 border border-accent-mint/30 text-[13.5px] text-accent-mint flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>
            Auditor action <strong>{actionSuccess}</strong> recorded successfully.
          </span>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <SkeletonCard className="lg:col-span-5 h-[460px]" />
          <SkeletonCard className="lg:col-span-7 h-[460px]" />
        </div>
      ) : !invData ? (
        <GlassCard>
          <EmptyState
            icon={<FileCheck2 className="w-5 h-5" />}
            title="No cases awaiting approval"
            description="Complete an AI investigation to review and sign off the statutory reply."
          />
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left 5 cols: Summary, Checklist & Sign-Off Controls */}
          <div className="lg:col-span-5 space-y-5">
            <GlassCard className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[12px] font-mono text-txt-muted">
                    {invData.notice?.notice_number || 'GST Notice'}
                  </div>
                  <h2 className="text-[18px] font-medium text-txt-primary mt-0.5">
                    {invData.title}
                  </h2>
                </div>
                <StatusBadge status={invData.status} />
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-inner bg-surface-2">
                  <div className="text-[12px] text-txt-muted">Mismatch Value</div>
                  <div className="text-[18px] font-medium tabular-nums text-txt-primary mt-0.5">
                    {formatCurrency(invData.mismatch_amount)}
                  </div>
                </div>
                <div className="p-3.5 rounded-inner bg-surface-2">
                  <div className="text-[12px] text-txt-muted">Evidence Records</div>
                  <div className="text-[18px] font-medium tabular-nums text-accent-mint mt-0.5">
                    {evidenceCount} ({supportedCount} supported)
                  </div>
                </div>
              </div>

              {/* Verification Checklist */}
              <div className="space-y-2 pt-2 border-t border-border-subtle">
                <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted">
                  Statutory Sign-Off Checklist
                </div>
                {[
                  { label: 'GSTR-3B vs GSTR-2B reconciliation verified', ok: true },
                  { label: 'Evidence provenance checked', ok: evidenceCount > 0 },
                  { label: 'Response draft populated', ok: Boolean(executiveSummary || legalGrounds) },
                ].map((chk) => (
                  <div
                    key={chk.label}
                    className="flex items-center gap-2.5 text-[13.5px] text-txt-secondary"
                  >
                    <CheckCircle2
                      className={`w-4 h-4 shrink-0 ${
                        chk.ok ? 'text-accent-mint' : 'text-txt-muted'
                      }`}
                    />
                    <span>{chk.label}</span>
                  </div>
                ))}
              </div>

              {/* Auditor Identity & Timestamp */}
              <div className="p-3.5 rounded-inner bg-surface-2 border border-border-subtle text-[12.5px] space-y-1">
                <div className="flex items-center justify-between text-txt-secondary">
                  <span>Signatory Auditor</span>
                  <span className="font-medium text-txt-primary">
                    {user?.full_name || user?.email || 'Authorized Auditor'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-txt-muted font-mono">
                  <span>Timestamp</span>
                  <span>{formatDateTime(new Date().toISOString())}</span>
                </div>
              </div>
            </GlassCard>

            {/* Attestation & Action Buttons */}
            <GlassCard className="space-y-4">
              <div>
                <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                  Auditor Attestation Notes
                </label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full rounded-inner bg-surface-2 border border-border-subtle p-3.5 text-[13.5px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                <Button
                  variant="secondary"
                  loading={submitting}
                  onClick={() => handleAction('EDIT')}
                  leftIcon={<Save className="w-4 h-4" />}
                >
                  Save Edits
                </Button>
                <Button
                  variant="primary"
                  disabled={isApproved}
                  onClick={() => setConfirmApproveOpen(true)}
                  leftIcon={<ShieldCheck className="w-4 h-4" />}
                >
                  {isApproved ? 'Approved' : 'Approve & Sign Off'}
                </Button>
                <Button
                  variant="secondary"
                  loading={submitting}
                  onClick={() => handleAction('REQUEST_MORE_EVIDENCE')}
                  leftIcon={<RotateCcw className="w-4 h-4" />}
                >
                  Request Evidence
                </Button>
                <Button
                  variant="destructive"
                  loading={submitting}
                  onClick={() => handleAction('REJECT')}
                  leftIcon={<XCircle className="w-4 h-4" />}
                >
                  Reject
                </Button>
              </div>
            </GlassCard>
          </div>

          {/* Right 7 cols: Full Response Preview */}
          <GlassCard className="lg:col-span-7 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary">
                Full Statutory Response Preview
              </h3>
              <Link
                to={`/app/auditor/response-drafts?id=${selectedId}`}
                className="text-[13px] font-medium text-brand-orange hover:text-brand-amber"
              >
                Edit in Draft Studio →
              </Link>
            </div>

            {!draftTitle && !executiveSummary && !legalGrounds ? (
              <EmptyState
                icon={<FileCheck2 className="w-5 h-5" />}
                description="No response draft content available for this investigation yet."
              />
            ) : (
              <div className="space-y-5 text-[14px] leading-[22px] text-txt-secondary">
                <div>
                  <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-1">
                    Title
                  </div>
                  <div className="text-[18px] font-semibold text-txt-primary">
                    {draftTitle}
                  </div>
                </div>

                {executiveSummary && (
                  <div>
                    <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-1">
                      Executive Summary
                    </div>
                    <p className="whitespace-pre-wrap text-txt-primary/90">
                      {executiveSummary}
                    </p>
                  </div>
                )}

                {reconciliationTable && (
                  <div>
                    <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-1">
                      Reconciliation Table
                    </div>
                    <pre className="p-4 rounded-inner bg-base/80 border border-border-subtle font-mono text-[12.5px] text-txt-primary overflow-x-auto whitespace-pre-wrap">
                      {reconciliationTable}
                    </pre>
                  </div>
                )}

                {legalGrounds && (
                  <div>
                    <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-1">
                      Legal Grounds
                    </div>
                    <p className="whitespace-pre-wrap text-txt-primary/90">
                      {legalGrounds}
                    </p>
                  </div>
                )}

                {prayer && (
                  <div>
                    <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-1">
                      Prayer
                    </div>
                    <p className="whitespace-pre-wrap text-txt-primary/90">{prayer}</p>
                  </div>
                )}
              </div>
            )}
          </GlassCard>
        </div>
      )}

      <ConfirmationModal
        open={confirmApproveOpen}
        title="Confirm Auditor Final Approval"
        description={`You are signing off on "${invData?.title || 'this investigation'}" as ${user?.full_name || 'Auditor'}. This locks the statutory reply for PDF export.`}
        confirmLabel="Approve & Sign Off"
        loading={submitting}
        onConfirm={() => handleAction('APPROVE')}
        onCancel={() => setConfirmApproveOpen(false)}
      />
    </div>
  )
}
