import React, { useEffect, useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '@/services/api/client'
import { Scale, AlertTriangle, FileText } from 'lucide-react'
import {
  GlassCard,
  SegmentedControl,
  StatusBadge,
  EmptyState,
  SkeletonCard,
  PageHeader,
} from '@/components/ui'

export function AuditorEvidencePage() {
  const [searchParams] = useSearchParams()
  const paramId = searchParams.get('id')

  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramId || '')
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

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
    async function loadEvidence() {
      setLoading(true)
      try {
        const res = await api.get(`/investigations/${selectedId}/evidence`)
        if (res.data.success) {
          setEvidenceData(res.data.data)
        }
      } catch (e) {
        console.error('Failed to load evidence', e)
      } finally {
        setLoading(false)
      }
    }
    loadEvidence()
  }, [selectedId])

  const records = evidenceData?.evidence_records || []

  const counts = useMemo(() => {
    const getSt = (r: any) => (r.status || r.verification_status || 'SUPPORTED').toUpperCase()
    return {
      ALL: records.length,
      SUPPORTED: records.filter((r: any) => getSt(r) === 'SUPPORTED').length,
      CONTRADICTED: records.filter((r: any) => getSt(r) === 'CONTRADICTED').length,
      UNVERIFIED: records.filter((r: any) => getSt(r) === 'UNVERIFIED').length,
    }
  }, [records])

  const filtered = useMemo(() => {
    if (statusFilter === 'ALL') return records
    return records.filter(
      (r: any) => (r.status || r.verification_status || 'SUPPORTED').toUpperCase() === statusFilter
    )
  }, [records, statusFilter])

  return (
    <div className="space-y-5">
      <PageHeader
        title="Evidence & Findings"
        subtitle="Audit-grade evidence records collected from tax portals, purchase ledgers, and e-way bills."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Evidence' },
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
                {i.title}
              </option>
            ))}
          </select>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <SegmentedControl
          value={statusFilter}
          onChange={setStatusFilter}
          options={[
            { value: 'ALL', label: `All (${counts.ALL})` },
            { value: 'SUPPORTED', label: `Supported (${counts.SUPPORTED})` },
            { value: 'CONTRADICTED', label: `Contradicted (${counts.CONTRADICTED})` },
            { value: 'UNVERIFIED', label: `Unverified (${counts.UNVERIFIED})` },
          ]}
        />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <SkeletonCard className="h-44" />
          <SkeletonCard className="h-44" />
        </div>
      ) : filtered.length === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Scale className="w-5 h-5" />}
            title="No evidence records"
            description="No evidence records match this filter for the selected investigation."
          />
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((rec: any, idx: number) => {
            const st = (rec.status || rec.verification_status || 'SUPPORTED').toUpperCase()
            const isMissing = st === 'UNVERIFIED' || st === 'CONTRADICTED'
            return (
              <GlassCard key={rec.id || idx} className="flex flex-col justify-between gap-4">
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-surface-2 border border-border-subtle flex items-center justify-center text-brand-orange shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-[15px] font-medium text-txt-primary truncate">
                          {rec.evidence_type || rec.source_type || 'Evidence Record'}
                        </div>
                        <div className="text-[12px] font-mono tabular-nums text-txt-muted truncate">
                          {rec.source_tool || rec.source || 'FastMCP Verification'}
                        </div>
                      </div>
                    </div>
                    <StatusBadge status={st} />
                  </div>

                  <p className="text-[13.5px] leading-[20px] text-txt-secondary">
                    {rec.summary || rec.description || JSON.stringify(rec.details || rec.data || {})}
                  </p>

                  {isMissing && (
                    <div className="p-3 rounded-inner bg-warning/10 border border-warning/30 text-[12.5px] text-warning flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>
                        {rec.missing_evidence ||
                          'Supporting document requires auditor verification or supplier confirmation.'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[12px] font-mono tabular-nums text-txt-muted">
                  <span>Invoice: {rec.invoice_number || rec.invoice_ref || '—'}</span>
                  <span>Supplier: {rec.supplier_gstin || '—'}</span>
                </div>
              </GlassCard>
            )
          })}
        </div>
      )}
    </div>
  )
}
