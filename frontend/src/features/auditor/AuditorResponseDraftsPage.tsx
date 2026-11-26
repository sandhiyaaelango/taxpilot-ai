import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatDateTime } from '@/utils'
import {
  Save,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Eye,
} from 'lucide-react'
import {
  GlassCard,
  Button,
  Input,
  StatusBadge,
  EmptyState,
  SkeletonCard,
  PageHeader,
} from '@/components/ui'

export function AuditorResponseDraftsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const paramId = searchParams.get('id')

  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramId || '')
  const [invData, setInvData] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [noDraftFound, setNoDraftFound] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [dirty, setDirty] = useState(false)
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null)

  const [responseTitle, setResponseTitle] = useState('')
  const [executiveSummary, setExecutiveSummary] = useState('')
  const [reconciliationTable, setReconciliationTable] = useState('')
  const [legalGrounds, setLegalGrounds] = useState('')
  const [prayer, setPrayer] = useState('')
  const [missingDisclosures, setMissingDisclosures] = useState<string[]>([])

  useEffect(() => {
    async function loadList() {
      try {
        const res = await api.get('/investigations?page_size=50')
        if (res.data.success && res.data.data.length > 0) {
          setInvestigations(res.data.data)
          if (!selectedId) {
            setSelectedId(res.data.data[0].id)
          }
        }
      } catch (e) {
        console.error('Failed to load investigations', e)
      }
    }
    loadList()
  }, [])

  const loadReport = async (id: string) => {
    if (!id) return
    setLoading(true)
    setNoDraftFound(false)
    setSaveError(null)
    try {
      const invRes = await api.get(`/investigations/${id}`)
      if (invRes.data.success) {
        setInvData(invRes.data.data)
      }
      const res = await api.get(`/reports/${id}`)
      if (res.data.success && res.data.data) {
        const r = res.data.data
        setReport(r)
        const c = r.content || {}
        setResponseTitle(c.title || r.title || '')
        setExecutiveSummary(c.executive_summary || '')
        setReconciliationTable(c.reconciliation_table || '')
        setLegalGrounds(c.legal_grounds || c.legal_submissions || '')
        setPrayer(c.prayer || '')
        setMissingDisclosures(c.missing_document_disclosures || [])
        setLastSavedAt(c.updated_at || r.updated_at || r.created_at || null)
        setDirty(false)
      }
    } catch (e: any) {
      setReport(null)
      setResponseTitle('')
      setExecutiveSummary('')
      setReconciliationTable('')
      setLegalGrounds('')
      setPrayer('')
      setMissingDisclosures([])
      if (e.response?.status === 404) {
        setNoDraftFound(true)
      } else {
        setSaveError(e.response?.data?.detail || 'Failed to load response draft from backend.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedId) loadReport(selectedId)
  }, [selectedId])

  const handleSelectCase = (id: string) => {
    setSelectedId(id)
    setSearchParams({ id })
  }

  const handleSaveDraft = async () => {
    if (!selectedId) return
    setSaving(true)
    setSaveSuccess(false)
    setSaveError(null)
    try {
      const nowIso = new Date().toISOString()
      const payload = {
        action: 'EDIT',
        notes: 'Auditor modified draft response text and annexures.',
        edited_content: {
          title: responseTitle,
          executive_summary: executiveSummary,
          legal_grounds: legalGrounds,
          legal_submissions: legalGrounds,
          reconciliation_table: reconciliationTable,
          prayer,
          updated_at: nowIso,
        },
      }
      const res = await api.post(`/approvals/${selectedId}`, payload)
      if (res.data.success) {
        setSaveSuccess(true)
        setDirty(false)
        setLastSavedAt(nowIso)
        await loadReport(selectedId)
        setTimeout(() => setSaveSuccess(false), 3500)
      }
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || 'Failed to save draft changes to backend.')
    } finally {
      setSaving(false)
    }
  }

  const sections = [
    { id: 'sec-title', label: '1. Response Title' },
    { id: 'sec-summary', label: '2. Executive Summary' },
    { id: 'sec-table', label: '3. Annexure Table' },
    { id: 'sec-legal', label: '4. Legal Grounds' },
    { id: 'sec-prayer', label: '5. Prayer & Relief' },
  ]

  return (
    <div className="space-y-5">
      <PageHeader
        title="Response Drafts"
        subtitle="Edit statutory GST notice reply sections with real-time preview and database persistence."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Response Drafts' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <select
              aria-label="Select investigation"
              value={selectedId}
              onChange={(e) => handleSelectCase(e.target.value)}
              className="h-11 px-4 rounded-full bg-surface-2 border border-border-subtle text-[13.5px] font-medium text-txt-primary focus:outline-none focus:border-brand-orange/70 min-w-[220px]"
            >
              {investigations.map((i) => (
                <option key={i.id} value={i.id} className="bg-elevated text-txt-primary">
                  {i.title} ({i.status})
                </option>
              ))}
            </select>
            <Button
              variant="secondary"
              loading={saving}
              disabled={!selectedId || noDraftFound}
              onClick={handleSaveDraft}
              leftIcon={<Save className="w-4 h-4" />}
            >
              {saving ? 'Saving...' : 'Save Draft'}
            </Button>
            {selectedId && (
              <Link to={`/app/auditor/pending-review?id=${selectedId}`}>
                <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  Proceed to Approval
                </Button>
              </Link>
            )}
          </div>
        }
      />

      {/* Save State Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1 text-[13px]">
        <div className="flex items-center gap-2.5">
          {invData?.status && <StatusBadge status={invData.status} />}
          {dirty ? (
            <span className="text-brand-amber font-medium">Unsaved changes</span>
          ) : saveSuccess ? (
            <span className="text-accent-mint font-medium flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Saved to database
            </span>
          ) : (
            <span className="text-txt-muted">All changes synced</span>
          )}
        </div>
        {lastSavedAt && (
          <span className="text-[12px] font-mono text-txt-muted">
            Last saved: {formatDateTime(lastSavedAt)}
          </span>
        )}
      </div>

      {saveError && (
        <div
          role="alert"
          className="p-4 rounded-inner bg-danger/12 border border-danger/30 text-[13.5px] text-danger flex items-center gap-2"
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      {missingDisclosures.length > 0 && (
        <div className="p-4 rounded-inner bg-warning/10 border border-warning/30 text-[13px] text-warning space-y-1">
          <div className="font-medium">Missing Evidence Disclosures Noted in Draft</div>
          <ul className="list-disc pl-5 text-[12.5px] text-txt-secondary">
            {missingDisclosures.map((d, idx) => (
              <li key={idx}>{d}</li>
            ))}
          </ul>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <SkeletonCard className="lg:col-span-7 h-[460px]" />
          <SkeletonCard className="lg:col-span-5 h-[460px]" />
        </div>
      ) : noDraftFound ? (
        <GlassCard>
          <EmptyState
            icon={<FileText className="w-5 h-5" />}
            title="No response draft generated yet"
            description="Run the AI investigation pipeline first so the Response Drafter agent can generate a statutory reply."
            action={
              selectedId && (
                <Link to={`/app/auditor/monitoring?id=${selectedId}`}>
                  <Button variant="primary" size="sm">
                    Open AI Monitoring
                  </Button>
                </Link>
              )
            }
          />
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
          {/* Left 2 cols: Sticky Section Outline */}
          <GlassCard padding="sm" className="xl:col-span-2 xl:sticky xl:top-4 hidden xl:block">
            <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted px-2 mb-2.5">
              Outline
            </div>
            <nav className="space-y-1">
              {sections.map((s) => (
                <a
                  key={s.id}
                  href={`#${s.id}`}
                  className="block px-2.5 py-2 rounded-xl text-[13px] text-txt-secondary hover:text-txt-primary hover:bg-surface-2 transition-colors"
                >
                  {s.label}
                </a>
              ))}
            </nav>
          </GlassCard>

          {/* Center 5 cols: Section Editors */}
          <GlassCard className="xl:col-span-5 space-y-5">
            <h2 className="text-[18px] leading-[24px] font-medium text-txt-primary">
              Draft Editor
            </h2>

            <div id="sec-title">
              <Input
                label="Response Title"
                value={responseTitle}
                onChange={(e) => {
                  setResponseTitle(e.target.value)
                  setDirty(true)
                }}
                placeholder="Reply to Form GST DRC-01A..."
              />
            </div>

            <div id="sec-summary">
              <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                Executive Summary &amp; Factual Submissions
              </label>
              <textarea
                rows={5}
                value={executiveSummary}
                onChange={(e) => {
                  setExecutiveSummary(e.target.value)
                  setDirty(true)
                }}
                className="w-full rounded-inner bg-surface-2 border border-border-subtle p-3.5 text-[14px] leading-[22px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>

            <div id="sec-table">
              <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                Annexure Reconciliation Table
              </label>
              <textarea
                rows={5}
                value={reconciliationTable}
                onChange={(e) => {
                  setReconciliationTable(e.target.value)
                  setDirty(true)
                }}
                className="w-full rounded-inner bg-surface-2 border border-border-subtle p-3.5 text-[13px] font-mono leading-[20px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>

            <div id="sec-legal">
              <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                Legal Grounds &amp; Statutory Citations
              </label>
              <textarea
                rows={6}
                value={legalGrounds}
                onChange={(e) => {
                  setLegalGrounds(e.target.value)
                  setDirty(true)
                }}
                className="w-full rounded-inner bg-surface-2 border border-border-subtle p-3.5 text-[14px] leading-[22px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>

            <div id="sec-prayer">
              <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                Prayer &amp; Relief Sought
              </label>
              <textarea
                rows={4}
                value={prayer}
                onChange={(e) => {
                  setPrayer(e.target.value)
                  setDirty(true)
                }}
                className="w-full rounded-inner bg-surface-2 border border-border-subtle p-3.5 text-[14px] leading-[22px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>
          </GlassCard>

          {/* Right 5 cols: Live Statutory Preview */}
          <GlassCard className="xl:col-span-5 space-y-4 xl:sticky xl:top-4">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2 text-[15px] font-medium text-txt-primary">
                <Eye className="w-4 h-4 text-accent-mint" />
                <span>Live Statutory Preview</span>
              </div>
              {report?.version && (
                <span className="text-[12px] font-mono text-txt-muted">
                  v{report.version}
                </span>
              )}
            </div>

            <div className="space-y-4 text-[14px] leading-[22px] text-txt-secondary max-h-[680px] overflow-y-auto pr-1">
              <h3 className="text-[18px] font-semibold text-txt-primary">
                {responseTitle || 'Untitled Statutory Reply'}
              </h3>

              {executiveSummary && (
                <div className="space-y-1">
                  <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted">
                    Executive Summary
                  </div>
                  <p className="whitespace-pre-wrap text-txt-primary/90">{executiveSummary}</p>
                </div>
              )}

              {reconciliationTable && (
                <div className="space-y-1">
                  <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted">
                    Reconciliation Annexure
                  </div>
                  <pre className="p-3.5 rounded-inner bg-base/80 border border-border-subtle font-mono text-[12.5px] text-txt-primary overflow-x-auto whitespace-pre-wrap">
                    {reconciliationTable}
                  </pre>
                </div>
              )}

              {legalGrounds && (
                <div className="space-y-1">
                  <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted">
                    Legal Grounds
                  </div>
                  <p className="whitespace-pre-wrap text-txt-primary/90">{legalGrounds}</p>
                </div>
              )}

              {prayer && (
                <div className="space-y-1">
                  <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted">
                    Prayer
                  </div>
                  <p className="whitespace-pre-wrap text-txt-primary/90">{prayer}</p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
