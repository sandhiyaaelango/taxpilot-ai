import React, { useEffect, useState, useRef, useMemo } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency } from '@/utils'
import {
  Activity,
  Compass,
  Layers,
  Search,
  Scale,
  ShieldCheck,
  FileCheck2,
  ArrowRight,
  Wrench,
  Pause,
  Play,
  Clock,
  Server,
} from 'lucide-react'
import {
  GlassCard,
  Button,
  StatusBadge,
  EmptyState,
  PageHeader,
} from '@/components/ui'

export function AuditorAiMonitoringPage() {
  const [searchParams] = useSearchParams()
  const investigationId = searchParams.get('id')

  const [investigations, setInvestigations] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string>(investigationId || '')
  const [invData, setInvData] = useState<any>(null)
  const [sseEvents, setSseEvents] = useState<any[]>([])
  const [connectionStatus, setConnectionStatus] = useState<'CONNECTED' | 'CONNECTING' | 'DISCONNECTED'>('CONNECTING')
  const [lastUpdated, setLastUpdated] = useState<string>(new Date().toLocaleTimeString())
  const [pauseLogs, setPauseLogs] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const sseContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    async function loadList() {
      try {
        const res = await api.get('/investigations?page_size=20')
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

  useEffect(() => {
    if (!selectedId) return
    let eventSource: EventSource | null = null
    let pollInterval: any = null

    async function fetchDetails() {
      try {
        const res = await api.get(`/investigations/${selectedId}`)
        if (res.data.success) {
          setInvData(res.data.data)
          setLastUpdated(new Date().toLocaleTimeString())
        }
      } catch (e) {
        console.error('Failed to fetch details', e)
      }
    }

    fetchDetails()

    try {
      setConnectionStatus('CONNECTING')
      eventSource = new EventSource(`/api/v1/investigations/${selectedId}/stream`)

      eventSource.onopen = () => {
        setConnectionStatus('CONNECTED')
      }

      eventSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          if (!pauseLogs) {
            setSseEvents((prev) => [
              { ...parsed, receivedAt: new Date().toLocaleTimeString() },
              ...prev.slice(0, 49),
            ])
          }
          setLastUpdated(new Date().toLocaleTimeString())

          if (
            parsed.event === 'agent_started' ||
            parsed.event === 'agent_completed' ||
            parsed.event === 'agent_failed' ||
            parsed.event === 'node_transition' ||
            parsed.event === 'mismatch_items_extracted' ||
            parsed.event === 'verification_gate_evaluated' ||
            parsed.event === 'investigation_paused_for_approval' ||
            parsed.event === 'investigation_completed'
          ) {
            fetchDetails()
          }
        } catch {
          // ignore parse errors
        }
      }

      eventSource.onerror = () => {
        setConnectionStatus('DISCONNECTED')
      }
    } catch {
      setConnectionStatus('DISCONNECTED')
    }

    pollInterval = setInterval(() => {
      fetchDetails()
    }, 3000)

    return () => {
      if (eventSource) eventSource.close()
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [selectedId, pauseLogs])

  // Live elapsed timer when investigation is running
  const isRunningStatus = [
    'PARSING_NOTICE',
    'VALIDATING_NOTICE',
    'BUILDING_PLAN',
    'INVESTIGATING',
    'CHALLENGING_EVIDENCE',
    'VERIFYING',
    'DRAFTING_RESPONSE',
  ].includes(invData?.status)

  useEffect(() => {
    if (!invData) return
    const firstStart = invData.agent_runs?.[0]?.started_at || invData.created_at
    if (!firstStart) return

    const updateTimer = () => {
      const startMs = new Date(firstStart).getTime()
      const diff = Math.max(0, Math.floor((Date.now() - startMs) / 1000))
      setElapsedSeconds(diff)
    }
    updateTimer()
    if (!isRunningStatus) return
    const id = setInterval(updateTimer, 1000)
    return () => clearInterval(id)
  }, [invData, isRunningStatus])

  const runs = invData?.agent_runs || []
  const findRun = (namePart: string) =>
    runs.find((r: any) => (r.agent_name || '').toLowerCase().includes(namePart.toLowerCase()))

  const getStageStatus = (
    run: any,
    fallback?: string
  ): 'COMPLETED' | 'RUNNING' | 'FAILED' | 'PENDING' => {
    if (run) {
      const s = run.status?.toUpperCase()
      if (['COMPLETED', 'RUNNING', 'FAILED'].includes(s)) return s as any
    }
    return (fallback as any) || 'PENDING'
  }

  const supervisorRun = findRun('supervisor')
  const ledgerRun = findRun('ledger')
  const rootRun = findRun('root')
  const challengeRun = findRun('challenge')
  const verificationRun = findRun('verification')
  const drafterRun = findRun('drafter') || findRun('response')

  const stages = [
    {
      id: 'supervisor',
      name: 'Supervisor Agent',
      role: 'Planning & Dispatch',
      icon: Compass,
      status: getStageStatus(
        supervisorRun,
        invData?.status && invData?.status !== 'PENDING' ? 'COMPLETED' : 'PENDING'
      ),
      details:
        supervisorRun?.summary ||
        supervisorRun?.agent_metadata?.output_summary ||
        'Decomposes GST notice into mismatch tasks and dispatches ReAct loops.',
      error: supervisorRun?.error_message,
      duration_ms: supervisorRun?.duration_ms,
      tool_calls: supervisorRun?.tool_calls || [],
    },
    {
      id: 'ledger',
      name: 'Ledger Matcher',
      role: 'GSTR-2B vs 3B Reconciliation',
      icon: Layers,
      status: getStageStatus(ledgerRun),
      details:
        ledgerRun?.summary ||
        ledgerRun?.agent_metadata?.output_summary ||
        'Queries purchase ledgers and GSTR-2B via FastMCP tools.',
      error: ledgerRun?.error_message,
      duration_ms: ledgerRun?.duration_ms,
      tool_calls: ledgerRun?.tool_calls || [],
    },
    {
      id: 'root_cause',
      name: 'Root-Cause Investigator',
      role: 'Hypothesis Validation',
      icon: Search,
      status: getStageStatus(rootRun),
      details:
        rootRun?.summary ||
        rootRun?.agent_metadata?.output_summary ||
        'Evaluates timing differences, supplier non-filing, and duplicate entries.',
      error: rootRun?.error_message,
      duration_ms: rootRun?.duration_ms,
      tool_calls: rootRun?.tool_calls || [],
    },
    {
      id: 'challenge',
      name: 'Evidence Challenge',
      role: 'Contradiction & Provenance',
      icon: Scale,
      status: getStageStatus(challengeRun),
      details:
        challengeRun?.summary ||
        challengeRun?.agent_metadata?.output_summary ||
        'Audits evidence veracity and isolates unsupported ITC claims.',
      error: challengeRun?.error_message,
      duration_ms: challengeRun?.duration_ms,
      tool_calls: challengeRun?.tool_calls || [],
    },
    {
      id: 'verification',
      name: 'Verification Gate',
      role: 'Deterministic Policy Check',
      icon: ShieldCheck,
      status: getStageStatus(
        verificationRun,
        ['AWAITING_APPROVAL', 'APPROVED'].includes(invData?.status) ? 'COMPLETED' : undefined
      ),
      details:
        verificationRun?.summary ||
        verificationRun?.agent_metadata?.output_summary ||
        'Enforces arithmetic precision and CBIC Circular 183/15/2022-GST.',
      error: verificationRun?.error_message,
      duration_ms: verificationRun?.duration_ms,
      tool_calls: verificationRun?.tool_calls || [],
    },
    {
      id: 'drafter',
      name: 'Response Drafter',
      role: 'Reply & Annexures',
      icon: FileCheck2,
      status: getStageStatus(
        drafterRun,
        ['AWAITING_APPROVAL', 'APPROVED'].includes(invData?.status) ? 'COMPLETED' : undefined
      ),
      details:
        drafterRun?.summary ||
        drafterRun?.agent_metadata?.output_summary ||
        'Compiles statutory reply draft with invoice annexures.',
      error: drafterRun?.error_message,
      duration_ms: drafterRun?.duration_ms,
      tool_calls: drafterRun?.tool_calls || [],
    },
  ]

  const allToolCalls = useMemo(() => {
    const items: any[] = []
    for (const st of stages) {
      for (const tc of st.tool_calls || []) {
        items.push({
          agent: st.name,
          tool_name: tc.tool_name || tc.name || 'FastMCP Tool',
          status: tc.status || 'COMPLETED',
          timestamp: tc.timestamp || tc.started_at || lastUpdated,
          error: tc.error || tc.error_message,
          output: tc.output_summary || tc.result,
        })
      }
    }
    return items
  }, [stages, lastUpdated])

  const mismatchList =
    invData?.workflow_state?.mismatch_results ||
    invData?.workflow_state?.mismatch_items ||
    []

  const formatElapsed = (sec: number) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="AI Investigation Monitoring"
        subtitle="Live LangGraph pipeline telemetry, mismatch fan-out tasks, and FastMCP tool execution."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'AI Monitoring' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-3">
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
            {selectedId && (
              <Link to={`/app/auditor/results?id=${selectedId}`}>
                <Button variant="primary" size="md" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  View Results
                </Button>
              </Link>
            )}
          </div>
        }
      />

      {/* Overall Status Hero */}
      <GlassCard className="relative overflow-hidden">
        {isRunningStatus && (
          <div
            aria-hidden="true"
            className="absolute -top-16 right-10 w-64 h-64 rounded-full bg-brand-orange/20 blur-[80px] pointer-events-none"
          />
        )}
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <StatusBadge status={invData?.status || 'PENDING'} />
              <StatusBadge
                status={
                  connectionStatus === 'CONNECTED'
                    ? 'ACTIVE'
                    : connectionStatus === 'CONNECTING'
                    ? 'RETRYING'
                    : 'PENDING'
                }
                label={
                  connectionStatus === 'CONNECTED'
                    ? 'SSE Live'
                    : connectionStatus === 'CONNECTING'
                    ? 'Connecting SSE'
                    : 'Polling Fallback'
                }
              />
              <span className="text-[12px] font-mono text-txt-muted">
                Updated {lastUpdated}
              </span>
            </div>
            <h2 className="text-[20px] font-medium text-txt-primary">
              {invData?.title || 'Select an investigation to monitor'}
            </h2>
          </div>

          <div className="flex items-center gap-6 shrink-0">
            <div className="text-right">
              <div className="text-[12px] text-txt-muted flex items-center justify-end gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span>Elapsed</span>
              </div>
              <div className="text-[24px] font-medium font-mono tabular-nums text-txt-primary">
                {formatElapsed(elapsedSeconds)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-[12px] text-txt-muted flex items-center justify-end gap-1">
                <Server className="w-3.5 h-3.5" />
                <span>FastMCP</span>
              </div>
              <div className="text-[13.5px] font-medium text-accent-mint">
                Portal &amp; Ledger Ready
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Connected 6-Stage Agent Pipeline */}
      <GlassCard>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary">
            Multi-Agent Execution Pipeline
          </h3>
          <span className="text-[12.5px] text-txt-muted font-mono tabular-nums">
            {stages.filter((s) => s.status === 'COMPLETED').length} / {stages.length} completed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {stages.map((stage, idx) => {
            const Icon = stage.icon
            const connectorClass =
              stage.status === 'COMPLETED'
                ? 'border-accent-mint/30 bg-accent-mint/[0.04]'
                : stage.status === 'RUNNING'
                ? 'border-brand-orange/45 bg-brand-orange/[0.06]'
                : stage.status === 'FAILED'
                ? 'border-danger/40 bg-danger/[0.06]'
                : 'border-border-subtle bg-surface-2/60'

            return (
              <div
                key={stage.id}
                className={`p-4 rounded-inner border transition-colors flex flex-col justify-between gap-3 ${connectorClass}`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                          stage.status === 'COMPLETED'
                            ? 'bg-accent-mint/15 text-accent-mint'
                            : stage.status === 'RUNNING'
                            ? 'bg-brand-orange/20 text-brand-orange animate-pulse'
                            : stage.status === 'FAILED'
                            ? 'bg-danger/15 text-danger'
                            : 'bg-surface-3 text-txt-muted'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-[14.5px] font-medium text-txt-primary truncate">
                          {idx + 1}. {stage.name}
                        </div>
                        <div className="text-[12px] text-txt-muted truncate">{stage.role}</div>
                      </div>
                    </div>
                    <StatusBadge status={stage.status} />
                  </div>

                  <p className="text-[13px] leading-[19px] text-txt-secondary line-clamp-2">
                    {stage.details}
                  </p>

                  {stage.error && (
                    <div className="p-2.5 rounded-xl bg-danger/12 border border-danger/30 text-[12px] font-mono text-danger">
                      {stage.error}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-border-subtle text-[12px] font-mono tabular-nums text-txt-muted">
                  <span>
                    {stage.duration_ms != null ? `${stage.duration_ms} ms` : '—'}
                  </span>
                  <span>
                    {stage.tool_calls?.length
                      ? `${stage.tool_calls.length} tool call(s)`
                      : 'No tool calls'}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </GlassCard>

      {/* Mismatch Fan-out Grid */}
      {mismatchList.length > 0 && (
        <GlassCard>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[18px] leading-[24px] font-medium text-txt-primary">
              Mismatch Fan-Out Tasks ({mismatchList.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {mismatchList.map((m: any) => (
              <div
                key={m.mismatch_id}
                className="p-4 rounded-inner bg-surface-2 border border-border-subtle flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="text-[14px] font-medium text-txt-primary font-mono tabular-nums truncate">
                    {m.mismatch_id} • {m.invoice_ref || 'Invoice'}
                  </div>
                  <div className="text-[12.5px] text-txt-secondary mt-0.5">
                    {m.classification || 'Unclassified'}
                  </div>
                  <div className="text-[14px] font-medium tabular-nums text-brand-amber mt-1.5">
                    {formatCurrency(m.mismatch_amount)}
                  </div>
                </div>
                <StatusBadge status={m.status || 'PENDING'} />
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Two-Column JetBrains Mono Logs: MCPToolLog & SSEEventLog */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* MCP Tool Log */}
        <GlassCard className="flex flex-col h-[380px]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[16px] font-medium text-txt-primary flex items-center gap-2">
              <Wrench className="w-4 h-4 text-brand-orange" />
              <span>MCP Tool Log</span>
            </h3>
            <span className="text-[12px] font-mono text-txt-muted">
              {allToolCalls.length} call(s)
            </span>
          </div>
          <div className="flex-1 overflow-y-auto rounded-inner bg-base/80 border border-border-subtle p-3.5 font-mono text-[13px] space-y-2">
            {allToolCalls.length === 0 ? (
              <EmptyState
                icon={<Wrench className="w-4 h-4" />}
                description="No MCP tool calls recorded for this investigation yet."
                className="h-full border-0 bg-transparent"
              />
            ) : (
              allToolCalls.map((tc, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-xl bg-surface-1 border border-border-subtle space-y-1"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-brand-orange font-medium">{tc.tool_name}</span>
                    <span className="text-[11.5px] text-txt-muted tabular-nums">
                      {tc.agent}
                    </span>
                  </div>
                  {tc.error && <div className="text-danger text-[12px]">{tc.error}</div>}
                  {tc.output && (
                    <div className="text-txt-secondary text-[12px] break-all">
                      {typeof tc.output === 'string' ? tc.output : JSON.stringify(tc.output)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </GlassCard>

        {/* SSE Event Log */}
        <GlassCard className="flex flex-col h-[380px]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[16px] font-medium text-txt-primary flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent-mint" />
              <span>SSE Event Log</span>
            </h3>
            <button
              type="button"
              onClick={() => setPauseLogs((p) => !p)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-2 border border-border-subtle hover:bg-surface-3 text-[12px] font-medium text-txt-secondary hover:text-txt-primary transition-colors"
            >
              {pauseLogs ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
              <span>{pauseLogs ? 'Resume' : 'Pause'}</span>
            </button>
          </div>
          <div
            ref={sseContainerRef}
            className="flex-1 overflow-y-auto rounded-inner bg-base/80 border border-border-subtle p-3.5 font-mono text-[13px] space-y-2"
          >
            {sseEvents.length === 0 ? (
              <EmptyState
                icon={<Activity className="w-4 h-4" />}
                description="Listening for real-time agent lifecycle events from the backend stream."
                className="h-full border-0 bg-transparent"
              />
            ) : (
              sseEvents.map((evt, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-xl bg-surface-1 border border-border-subtle space-y-1"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-brand-orange font-medium">
                      {evt.event || 'stream_event'}
                    </span>
                    <span className="text-[11.5px] text-txt-muted tabular-nums">
                      {evt.receivedAt || lastUpdated}
                    </span>
                  </div>
                  <div className="text-txt-secondary text-[12px] whitespace-pre-wrap break-all">
                    {typeof evt.data === 'string' ? evt.data : JSON.stringify(evt.data)}
                  </div>
                </div>
              ))
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
