import React, { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate } from '@/utils'
import { Search, Plus, FileSearch, ArrowUpRight, ArrowUpDown } from 'lucide-react'
import {
  GlassCard,
  Button,
  Input,
  FilterDropdown,
  DataTable,
  StatusBadge,
  EmptyState,
  ErrorState,
  SkeletonRow,
  PageHeader,
  type DataTableColumn,
} from '@/components/ui'

export function AuditorHistoryPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [investigations, setInvestigations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState(searchParams.get('q') || '')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortDesc, setSortDesc] = useState(true)

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ page_size: '100' })
      if (statusFilter) params.set('status', statusFilter)
      const res = await api.get(`/investigations?${params.toString()}`)
      if (res.data.success) {
        setInvestigations(res.data.data || [])
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load investigations from backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [statusFilter])

  const filtered = useMemo(() => {
    const list = investigations.filter((inv) => {
      if (!search.trim()) return true
      const term = search.toLowerCase()
      const noticeNo = inv.notice?.notice_number || ''
      const gstin = inv.notice?.gstin || inv.client_gstin || ''
      return (
        (inv.title || '').toLowerCase().includes(term) ||
        noticeNo.toLowerCase().includes(term) ||
        gstin.toLowerCase().includes(term) ||
        (inv.client_business_name || '').toLowerCase().includes(term)
      )
    })

    return [...list].sort((a, b) => {
      const tA = new Date(a.created_at || 0).getTime()
      const tB = new Date(b.created_at || 0).getTime()
      return sortDesc ? tB - tA : tA - tB
    })
  }, [investigations, search, sortDesc])

  const columns: DataTableColumn<any>[] = [
    {
      key: 'notice',
      header: 'Notice & Title',
      render: (inv) => (
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-surface-3 flex items-center justify-center text-brand-orange shrink-0">
            <FileSearch className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="font-medium text-txt-primary truncate">
              {inv.notice?.notice_number || inv.title}
            </div>
            <div className="text-[12px] text-txt-muted truncate">
              {inv.title}
            </div>
          </div>
        </div>
      ),
    },
    {
      key: 'gstin',
      header: 'Client / GSTIN',
      render: (inv) => (
        <div className="min-w-0">
          <div className="text-[13.5px] text-txt-primary truncate">
            {inv.client_business_name || 'Registered Taxpayer'}
          </div>
          <div className="text-[12px] font-mono tabular-nums text-txt-muted truncate">
            {inv.notice?.gstin || inv.client_gstin || '—'}
          </div>
        </div>
      ),
    },
    {
      key: 'period',
      header: 'Period',
      render: (inv) => (
        <span className="font-mono tabular-nums text-[13px] text-txt-secondary">
          {inv.tax_period || inv.notice?.tax_period || '—'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (inv) => <StatusBadge status={inv.status} />,
    },
    {
      key: 'amount',
      header: 'Mismatch',
      align: 'right',
      render: (inv) => (
        <span className="font-medium tabular-nums text-txt-primary">
          {formatCurrency(inv.mismatch_amount)}
        </span>
      ),
    },
    {
      key: 'updated',
      header: 'Created',
      align: 'right',
      render: (inv) => (
        <div className="flex items-center justify-end gap-2">
          <span className="text-[12.5px] text-txt-muted">{formatDate(inv.created_at)}</span>
          <ArrowUpRight className="w-4 h-4 text-txt-secondary" />
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-5">
      <PageHeader
        title="Investigations & History"
        subtitle="Track active AI pipelines, review completed reconciliations, and open archived cases."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Investigations' },
        ]}
        actions={
          <Button
            variant="primary"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => navigate('/app/auditor/new')}
          >
            New Investigation
          </Button>
        }
      />

      {/* Filter Bar */}
      <GlassCard padding="sm" className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by notice number, client, or GSTIN..."
              leftIcon={<Search className="w-4 h-4" />}
              className="h-10"
            />
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <FilterDropdown
              label="Status"
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: '', label: 'All Statuses' },
                { value: 'PENDING', label: 'Pending' },
                { value: 'INVESTIGATING', label: 'Investigating' },
                { value: 'AWAITING_APPROVAL', label: 'Awaiting Approval' },
                { value: 'APPROVED', label: 'Approved' },
                { value: 'NEEDS_MORE_EVIDENCE', label: 'Needs Evidence' },
                { value: 'REJECTED', label: 'Rejected' },
                { value: 'FAILED', label: 'Failed' },
              ]}
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setSortDesc((p) => !p)}
              leftIcon={<ArrowUpDown className="w-3.5 h-3.5" />}
            >
              {sortDesc ? 'Newest' : 'Oldest'}
            </Button>
          </div>
        </div>
      </GlassCard>

      {error && <ErrorState message={error} onRetry={fetchHistory} />}

      <GlassCard>
        {loading ? (
          <div className="space-y-2.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={filtered}
            keyExtractor={(inv) => inv.id}
            onRowClick={(inv) => {
              const activeStatuses = [
                'PARSING_NOTICE',
                'VALIDATING_NOTICE',
                'BUILDING_PLAN',
                'INVESTIGATING',
                'CHALLENGING_EVIDENCE',
                'VERIFYING',
                'DRAFTING_RESPONSE',
              ]
              if (activeStatuses.includes(inv.status)) {
                navigate(`/app/auditor/monitoring?id=${inv.id}`)
              } else {
                navigate(`/app/auditor/results?id=${inv.id}`)
              }
            }}
            emptyState={
              <EmptyState
                icon={<FileSearch className="w-5 h-5" />}
                title="No matching investigations"
                description="Try adjusting your search or status filter, or start a new GST notice investigation."
                action={
                  <Link to="/app/auditor/new">
                    <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
                      New Investigation
                    </Button>
                  </Link>
                }
              />
            }
          />
        )}
      </GlassCard>
    </div>
  )
}
