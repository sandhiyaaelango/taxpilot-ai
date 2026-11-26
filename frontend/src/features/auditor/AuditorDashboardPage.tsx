import React, { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatCompactCurrency, formatDate } from '@/utils'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'
import {
  Plus,
  ArrowUpRight,
  CalendarClock,
  FileSearch,
  Activity,
  Clock,
  CheckCircle2,
  ShieldCheck,
  Layers,
  ArrowUpDown,
} from 'lucide-react'
import {
  GlassCard,
  HeroCard,
  Button,
  SegmentedControl,
  StatusBadge,
  EmptyState,
  ErrorState,
  SkeletonCard,
  PageHeader,
} from '@/components/ui'

type RangeOption = '1y' | '6m' | '3m' | '1m'

export function AuditorDashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<any>(null)
  const [investigations, setInvestigations] = useState<any[]>([])
  const [atRiskDeadlines, setAtRiskDeadlines] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [range, setRange] = useState<RangeOption>('6m')
  const [barSortDesc, setBarSortDesc] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, invsRes, deadlinesRes] = await Promise.all([
        api.get('/analytics/dashboard'),
        api.get('/investigations?page_size=50'),
        api.get('/investigations/deadlines/at-risk').catch(() => ({ data: { data: [] } })),
      ])
      if (statsRes.data?.success) setStats(statsRes.data.data)
      if (invsRes.data?.success) setInvestigations(invsRes.data.data || [])
      if (deadlinesRes.data?.data) setAtRiskDeadlines(deadlinesRes.data.data.slice(0, 5))
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard metrics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const dist = stats?.status_distribution || {}
  const total = stats?.total_investigations ?? investigations.length
  const activeCount =
    (dist['INVESTIGATING'] || 0) +
    (dist['BUILDING_PLAN'] || 0) +
    (dist['CHALLENGING_EVIDENCE'] || 0) +
    (dist['VERIFYING'] || 0) +
    (dist['DRAFTING_RESPONSE'] || 0)
  const pendingCount = (dist['PENDING'] || 0) + (dist['PARSING_NOTICE'] || 0) + (dist['AWAITING_APPROVAL'] || 0)
  const completedCount = (dist['COMPLETED'] || 0) + (dist['AWAITING_APPROVAL'] || 0)
  const approvedCount = dist['APPROVED'] || 0

  const totalMismatch = useMemo(() => {
    return investigations.reduce((sum, inv) => sum + (Number(inv.mismatch_amount) || 0), 0)
  }, [investigations])

  // Build real time-series from investigations grouped by month
  const chartData = useMemo(() => {
    if (!investigations.length) return []
    const monthsToShow = range === '1y' ? 12 : range === '6m' ? 6 : range === '3m' ? 3 : 1
    const grouped = new Map<string, { label: string; count: number; mismatch: number; sortKey: string }>()

    for (const inv of investigations) {
      const d = inv.created_at ? new Date(inv.created_at) : new Date()
      const sortKey = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const label = d.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' })
      const prev = grouped.get(sortKey) || { label, count: 0, mismatch: 0, sortKey }
      prev.count += 1
      prev.mismatch += Number(inv.mismatch_amount) || 0
      grouped.set(sortKey, prev)
    }

    const sorted = Array.from(grouped.values())
      .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
      .slice(-monthsToShow)

    if (barSortDesc) {
      return [...sorted].sort((a, b) => b.mismatch - a.mismatch)
    }
    return sorted
  }, [investigations, range, barSortDesc])

  const maxMismatchPoint = useMemo(() => {
    if (!chartData.length) return null
    return chartData.reduce((max, item) => (item.mismatch > max.mismatch ? item : max), chartData[0])
  }, [chartData])

  const completedPct = total > 0 ? Math.round(((approvedCount + completedCount) / total) * 100) : 0
  const activePct = total > 0 ? Math.round((activeCount / total) * 100) : 0

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <SkeletonCard className="lg:col-span-8 h-[340px]" />
          <SkeletonCard className="lg:col-span-4 h-[340px]" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <SkeletonCard className="lg:col-span-3 h-[290px]" />
          <SkeletonCard className="lg:col-span-5 h-[290px]" />
          <SkeletonCard className="lg:col-span-4 h-[290px]" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-5">
        <PageHeader title="Auditor Dashboard" subtitle="GST notice reconciliation & verification overview" />
        <ErrorState message={error} onRetry={loadData} />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* Row 1: 8-col Area Chart + 4-col Upcoming GST Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Area Chart Card (8 cols) */}
        <GlassCard className="lg:col-span-8 flex flex-col justify-between min-h-[340px]">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
            <div>
              <div className="text-[15px] font-medium text-txt-secondary">
                Total Mismatch Investigated
              </div>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-[36px] leading-[42px] font-medium tabular-nums text-txt-primary tracking-tight">
                  {formatCurrency(totalMismatch)}
                </span>
                {total > 0 && (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-accent-green/12 text-accent-green text-[12.5px] font-medium tabular-nums">
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    <span>{total} cases</span>
                  </span>
                )}
              </div>
            </div>

            <SegmentedControl
              value={range}
              onChange={setRange}
              options={[
                { value: '1y', label: '1 year' },
                { value: '6m', label: '6 month' },
                { value: '3m', label: '3 month' },
                { value: '1m', label: '1 month' },
              ]}
            />
          </div>

          {chartData.length === 0 ? (
            <EmptyState
              icon={<Layers className="w-5 h-5" />}
              description="No investigation activity recorded yet. Upload a GST notice to populate trend metrics."
              className="my-auto py-8"
            />
          ) : (
            <>
              <div className="h-[190px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
                    <defs>
                      <linearGradient id="dashOrangeArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#FF6803" stopOpacity={0.55} />
                        <stop offset="100%" stopColor="#FF6803" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      stroke="rgba(255,255,255,0.06)"
                      strokeDasharray="4 4"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="label"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: 'rgba(255,255,255,0.40)', fontSize: 12 }}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v) => formatCompactCurrency(v)}
                      tick={{ fill: 'rgba(255,255,255,0.40)', fontSize: 12 }}
                      width={68}
                    />
                    <Tooltip
                      cursor={{ stroke: 'rgba(255,255,255,0.2)', strokeDasharray: '3 3' }}
                      content={({ active, payload, label }) => {
                        if (!active || !payload?.length) return null
                        return (
                          <div className="px-3.5 py-2 rounded-inner bg-white text-[#0F0703] shadow-xl">
                            <div className="text-[11.5px] font-medium text-[#0F0703]/65">{label}</div>
                            <div className="text-[14px] font-semibold tabular-nums">
                              {formatCurrency(Number(payload[0].value || 0))}
                            </div>
                          </div>
                        )
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="mismatch"
                      stroke="#FF6803"
                      strokeWidth={2}
                      fill="url(#dashOrangeArea)"
                      activeDot={{ r: 5, fill: '#FFFFFF', stroke: '#FF6803', strokeWidth: 2 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Thin segmented stage progress strip + bottom-right legend */}
              <div className="mt-4 pt-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1 h-1.5 rounded-full bg-surface-2 overflow-hidden flex">
                  <div
                    className="h-full bg-accent-mint transition-all duration-300"
                    style={{ width: `${Math.min(100, completedPct)}%` }}
                  />
                  <div
                    className="h-full bg-brand-orange transition-all duration-300"
                    style={{ width: `${Math.min(100 - completedPct, activePct)}%` }}
                  />
                </div>
                <div className="flex items-center gap-4 text-[12px] text-txt-secondary shrink-0">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-accent-mint" />
                    Verified ({approvedCount + completedCount})
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-sm bg-brand-orange" />
                    Active ({activeCount})
                  </span>
                </div>
              </div>
            </>
          )}
        </GlassCard>

        {/* Tall Right Card: Upcoming GST Deadlines (4 cols) */}
        <GlassCard className="lg:col-span-4 relative overflow-hidden flex flex-col justify-between min-h-[340px]">
          <div
            aria-hidden="true"
            className="absolute -top-12 -right-12 w-52 h-52 rounded-full bg-brand-orange/20 blur-[64px] pointer-events-none"
          />
          <div className="relative z-10 flex items-center justify-between mb-4">
            <h2 className="text-[18px] leading-[24px] font-medium text-txt-primary">
              Upcoming Deadlines
            </h2>
            <Link
              to="/app/auditor/my-investigations"
              className="text-[13px] text-txt-secondary hover:text-txt-primary transition-colors"
            >
              View All
            </Link>
          </div>

          <div className="relative z-10 flex-1 flex flex-col justify-center">
            {atRiskDeadlines.length === 0 ? (
              <EmptyState
                icon={<CalendarClock className="w-5 h-5" />}
                description="No urgent statutory deadlines on active notices."
                className="py-8"
              />
            ) : (
              <div className="space-y-2.5">
                {atRiskDeadlines.map((item: any) => (
                  <Link
                    key={item.investigation_id}
                    to={`/app/auditor/results?id=${item.investigation_id}`}
                    className="flex items-center justify-between gap-3 p-3.5 rounded-inner bg-surface-2 hover:bg-surface-3 border border-transparent hover:border-border-subtle transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-brand-orange/15 border border-brand-orange/25 flex items-center justify-center text-brand-orange shrink-0">
                        <CalendarClock className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-[13.5px] font-medium text-txt-primary truncate">
                          {item.title}
                        </div>
                        <div className="text-[12px] font-mono tabular-nums text-txt-muted truncate">
                          {item.client_gstin || item.response_deadline}
                        </div>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <StatusBadge
                        status={item.is_overdue ? 'FAILED' : 'RETRYING'}
                        label={item.is_overdue ? 'Overdue' : `${item.days_remaining}d left`}
                      />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Row 2: HeroCard (3 cols) + Bar Chart (5 cols) + Recent Investigations (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* HeroCard (3 cols) */}
        <HeroCard
          className="lg:col-span-3 min-h-[290px]"
          title="Start New Investigation"
          description="Upload a GST notice PDF to reconcile GSTR-3B vs GSTR-2B with evidence."
          action={
            <Button
              variant="white"
              size="md"
              className="w-full"
              leftIcon={<Plus className="w-4 h-4" />}
              onClick={() => navigate('/app/auditor/new')}
            >
              New Investigation
            </Button>
          }
        />

        {/* Bar Chart: Mismatch Amount by Month (5 cols) */}
        <GlassCard className="lg:col-span-5 flex flex-col justify-between min-h-[290px]">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div>
              <div className="text-[15px] font-medium text-txt-secondary">
                Mismatch by Period
              </div>
              <div className="text-[28px] leading-[34px] font-medium tabular-nums text-txt-primary mt-1">
                {formatCompactCurrency(totalMismatch)}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setBarSortDesc((p) => !p)}
              className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-full bg-surface-2 border border-border-subtle hover:bg-surface-3 text-[12.5px] font-medium text-txt-primary transition-colors"
            >
              <span>Sort</span>
              <ArrowUpDown className="w-3.5 h-3.5 text-txt-secondary" />
            </button>
          </div>

          {chartData.length === 0 ? (
            <EmptyState
              icon={<Layers className="w-5 h-5" />}
              description="No monthly mismatch breakdown available yet."
              className="my-auto py-6"
            />
          ) : (
            <div className="h-[185px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 18, right: 8, left: 8, bottom: 0 }}>
                  <defs>
                    <linearGradient id="mintBarGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#30FFAC" stopOpacity={1} />
                      <stop offset="100%" stopColor="#30FFAC" stopOpacity={0.15} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="label"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'rgba(255,255,255,0.40)', fontSize: 12 }}
                  />
                  <Tooltip
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                    content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null
                      return (
                        <div className="px-3 py-1.5 rounded-full bg-accent-mint text-[#0F0703] text-[12.5px] font-semibold tabular-nums shadow-lg">
                          {label}: {formatCompactCurrency(Number(payload[0].value || 0))}
                        </div>
                      )
                    }}
                  />
                  <Bar dataKey="mismatch" radius={[10, 10, 4, 4]} maxBarSize={44}>
                    {chartData.map((entry) => {
                      const isPeak = maxMismatchPoint && entry.sortKey === maxMismatchPoint.sortKey
                      return (
                        <Cell
                          key={entry.sortKey}
                          fill={isPeak ? 'url(#mintBarGrad)' : 'rgba(255, 255, 255, 0.08)'}
                        />
                      )
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </GlassCard>

        {/* Recent Investigations List (4 cols) */}
        <GlassCard className="lg:col-span-4 flex flex-col justify-between min-h-[290px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[18px] leading-[24px] font-medium text-txt-primary">
              Recent Investigations
            </h2>
            <Link
              to="/app/auditor/my-investigations"
              className="text-[13px] text-txt-secondary hover:text-txt-primary transition-colors"
            >
              View All
            </Link>
          </div>

          {investigations.length === 0 ? (
            <EmptyState
              icon={<FileSearch className="w-5 h-5" />}
              description="No investigations created yet."
              className="my-auto py-6"
            />
          ) : (
            <div className="space-y-2">
              {investigations.slice(0, 4).map((inv) => (
                <Link
                  key={inv.id}
                  to={`/app/auditor/results?id=${inv.id}`}
                  className="flex items-center justify-between gap-3 p-3 rounded-inner bg-surface-2 hover:bg-surface-3 border border-transparent hover:border-border-subtle transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-surface-3 flex items-center justify-center text-txt-primary shrink-0">
                      <FileSearch className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-[14px] font-medium text-txt-primary truncate">
                        {inv.notice?.notice_number || inv.title}
                      </div>
                      <div className="text-[12px] text-txt-muted truncate">
                        {formatDate(inv.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="text-[14px] font-medium tabular-nums text-accent-mint shrink-0">
                    {formatCurrency(inv.mismatch_amount)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Row 3: Compact 5 Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-5">
        {[
          {
            label: 'Total',
            value: total,
            icon: Layers,
            chip: 'All cases',
            chipClass: 'bg-surface-2 text-txt-secondary',
          },
          {
            label: 'Active',
            value: activeCount,
            icon: Activity,
            chip: 'AI running',
            chipClass: 'bg-brand-orange/12 text-brand-orange',
          },
          {
            label: 'Pending',
            value: pendingCount,
            icon: Clock,
            chip: 'Action needed',
            chipClass: 'bg-brand-amber/12 text-brand-amber',
          },
          {
            label: 'Completed',
            value: completedCount,
            icon: CheckCircle2,
            chip: 'Verified',
            chipClass: 'bg-accent-mint/12 text-accent-mint',
          },
          {
            label: 'Approved',
            value: approvedCount,
            icon: ShieldCheck,
            chip: 'Signed off',
            chipClass: 'bg-accent-green/12 text-accent-green',
          },
        ].map((stat) => {
          const Icon = stat.icon
          return (
            <GlassCard key={stat.label} padding="sm" className="p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="w-9 h-9 rounded-xl bg-surface-2 border border-border-subtle flex items-center justify-center text-txt-secondary">
                  <Icon className="w-4 h-4" />
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-[11.5px] font-medium ${stat.chipClass}`}>
                  {stat.chip}
                </span>
              </div>
              <div className="text-[32px] leading-[38px] font-medium tabular-nums text-txt-primary">
                {stat.value}
              </div>
              <div className="text-[13px] text-txt-secondary mt-0.5">{stat.label}</div>
            </GlassCard>
          )
        })}
      </div>
    </div>
  )
}
