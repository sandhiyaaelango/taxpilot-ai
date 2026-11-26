import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, formatDateTime } from '@/utils'
import { downloadReportPdf, extractApiErrorMessage } from '@/utils/pdfDownload'
import toast from 'react-hot-toast'
import { Download, ShieldCheck, FileText, AlertTriangle, Eye } from 'lucide-react'
import {
  GlassCard,
  Button,
  DataTable,
  StatusBadge,
  EmptyState,
  SkeletonRow,
  PageHeader,
  type DataTableColumn,
} from '@/components/ui'

export function AuditorApprovedReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const paramId = searchParams.get('id')

  const [approvedInvs, setApprovedInvs] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(paramId || '')
  const [invData, setInvData] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [approvals, setApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchApproved() {
      try {
        const res = await api.get('/investigations?status=APPROVED&page_size=50')
        if (res.data.success) {
          const list = res.data.data || []
          setApprovedInvs(list)
          if (!selectedId && list.length > 0) {
            setSelectedId(list[0].id)
          }
        }
      } catch (err) {
        console.error('Failed to load approved investigations', err)
      } finally {
        setLoading(false)
      }
    }
    fetchApproved()
  }, [])

  useEffect(() => {
    if (!selectedId) return
    async function loadData() {
      setError(null)
      try {
        const [invRes, repRes, appRes] = await Promise.all([
          api.get(`/investigations/${selectedId}`),
          api.get(`/reports/${selectedId}`),
          api.get(`/approvals/${selectedId}`),
        ])
        if (invRes.data.success) setInvData(invRes.data.data)
        if (repRes.data.success) setReport(repRes.data.data)
        if (appRes.data.success) setApprovals(appRes.data.data || [])
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Failed to load approved report details.')
      }
    }
    loadData()
  }, [selectedId])

  const handleDownloadPdf = async (id: string, noticeNumber?: string) => {
    if (!id || downloadingId) return
    setDownloadingId(id)
    setError(null)
    try {
      const filename = await downloadReportPdf(id, noticeNumber)
      toast.success(`Downloaded ${filename}`)
    } catch (err: any) {
      const msg = await extractApiErrorMessage(err, 'Failed to download PDF report.')
      setError(msg)
    } finally {
      setDownloadingId(null)
    }
  }

  const content = report?.content || invData?.workflow_state?.response_draft || {}
  const finalApproval = approvals.find((a) => a.action === 'APPROVE')

  const columns: DataTableColumn<any>[] = [
    {
      key: 'title',
      header: 'Approved Investigation',
      render: (inv) => (
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-accent-mint/12 text-accent-mint flex items-center justify-center shrink-0">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="font-medium text-txt-primary truncate">{inv.title}</div>
            <div className="text-[12px] font-mono text-txt-muted truncate">
              {inv.notice?.notice_number || inv.id.slice(0, 8)}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (inv) => <StatusBadge status={inv.status} />,
    },
    {
      key: 'amount',
      header: 'Variance',
      align: 'right',
      render: (inv) => (
        <span className="font-medium tabular-nums text-txt-primary">
          {formatCurrency(inv.mismatch_amount)}
        </span>
      ),
    },
    {
      key: 'date',
      header: 'Approved Date',
      align: 'right',
      render: (inv) => (
        <span className="text-[12.5px] text-txt-muted">
          {formatDate(inv.updated_at || inv.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (inv) => (
        <div
          className="flex items-center justify-end gap-2"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<Eye className="w-3.5 h-3.5" />}
            onClick={() => {
              setSelectedId(inv.id)
              setSearchParams({ id: inv.id })
            }}
          >
            View
          </Button>
          <Button
            size="sm"
            variant="primary"
            loading={downloadingId === inv.id}
            leftIcon={<Download className="w-3.5 h-3.5" />}
            onClick={() => handleDownloadPdf(inv.id)}
          >
            PDF
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-5">
      <PageHeader
        title="Approved Reports"
        subtitle="Signed statutory GST investigation packages ready for filing and PDF export."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Approved Reports' },
        ]}
      />

      {error && (
        <div
          role="alert"
          className="p-4 rounded-inner bg-danger/12 border border-danger/30 text-[13.5px] text-danger flex items-center gap-2"
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <GlassCard>
        {loading ? (
          <div className="space-y-2.5">
            <SkeletonRow />
            <SkeletonRow />
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={approvedInvs}
            keyExtractor={(inv) => inv.id}
            onRowClick={(inv) => {
              setSelectedId(inv.id)
              setSearchParams({ id: inv.id })
            }}
            emptyState={
              <EmptyState
                icon={<FileText className="w-5 h-5" />}
                title="No approved reports yet"
                description="Sign off an investigation on the Approval page to archive it here."
                action={
                  <Link to="/app/auditor/pending-review">
                    <Button variant="primary" size="sm">
                      Go to Approval Queue
                    </Button>
                  </Link>
                }
              />
            }
          />
        )}
      </GlassCard>

      {selectedId && invData && (
        <GlassCard className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border-subtle">
            <div>
              <h3 className="text-[18px] font-medium text-txt-primary">
                {content.title || invData.title}
              </h3>
              <div className="text-[12.5px] text-txt-muted mt-0.5">
                {finalApproval
                  ? `Approved on ${formatDateTime(finalApproval.created_at)}`
                  : `Updated ${formatDateTime(invData.updated_at)}`}
              </div>
            </div>
            <Button
              variant="primary"
              loading={downloadingId === selectedId}
              leftIcon={<Download className="w-4 h-4" />}
              onClick={() => handleDownloadPdf(selectedId)}
            >
              Download PDF
            </Button>
          </div>

          {content.executive_summary && (
            <p className="text-[14px] leading-[22px] text-txt-secondary whitespace-pre-wrap">
              {content.executive_summary}
            </p>
          )}
          {content.legal_grounds && (
            <p className="text-[14px] leading-[22px] text-txt-secondary whitespace-pre-wrap">
              {content.legal_grounds}
            </p>
          )}
        </GlassCard>
      )}
    </div>
  )
}
