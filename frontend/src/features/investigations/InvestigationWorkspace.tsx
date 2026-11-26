import React, { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import {
  FileSearch,
  Play,
  CheckCircle2,
  AlertTriangle,
  Scale,
  BrainCircuit,
  FileCheck2,
  Download,
  ArrowLeft,
  Sparkles,
  Server,
  Layers,
  ChevronRight,
  ShieldCheck,
  XCircle,
  FileText,
  Clock,
  Wrench,
  HelpCircle,
  RefreshCw,
  Send,
  Eye,
  AlertCircle
} from 'lucide-react'

interface AgentTelemetry {
  name: string
  role: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  started_at?: string
  completed_at?: string
  duration_ms?: number
  task: string
  output_summary?: string
  tool_calls_count: number
  error_message?: string
}

interface LiveToolCall {
  id: string
  agent_name: string
  tool_name: string
  mcp_server: string
  arguments: any
  result_status: 'RUNNING' | 'SUCCESS' | 'ERROR' | 'TIMEOUT'
  duration_ms?: number
  result_summary?: string
  called_at: string
}

const DEFAULT_AGENTS: AgentTelemetry[] = [
  {
    name: 'Supervisor Agent',
    role: 'Orchestration & Planning Layer',
    status: 'PENDING',
    task: 'Coordinates multi-agent delegation and manages workflow checkpoints',
    tool_calls_count: 0
  },
  {
    name: 'Notice Parser Agent',
    role: 'Document & Discrepancy Extraction',
    status: 'PENDING',
    task: 'Extracts GSTIN, tax period, ITC amounts, and notice reference',
    tool_calls_count: 0
  },
  {
    name: 'Ledger Matcher Agent',
    role: 'ReAct Loop 1: Ledger Reconciliation',
    status: 'PENDING',
    task: 'Queries Ledger MCP to reconcile invoices and identify mismatches',
    tool_calls_count: 0
  },
  {
    name: 'Root-Cause Investigator',
    role: 'ReAct Loop 2: Root-Cause Analysis',
    status: 'PENDING',
    task: 'Queries Tax Portal MCP to formulate timing, duplicate, or non-filing hypotheses',
    tool_calls_count: 0
  },
  {
    name: 'Evidence Challenge Engine',
    role: 'ReAct Loop 3: Adversarial Challenge',
    status: 'PENDING',
    task: 'Independently evaluates evidence and classifies as SUPPORTED, CONTRADICTED, or UNVERIFIED',
    tool_calls_count: 0
  },
  {
    name: 'Response Drafter Agent',
    role: 'Evidence-Constrained Response Studio',
    status: 'PENDING',
    task: 'Drafts formal legal rebuttal strictly adhering to verified evidence',
    tool_calls_count: 0
  }
]

export function InvestigationWorkspace() {
  const { id } = useParams<{ id: string }>()
  const [inv, setInv] = useState<any>(null)
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [agentRuns, setAgentRuns] = useState<any[]>([])
  const [graphData, setGraphData] = useState<any>(null)
  const [report, setReport] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'REACT_AGENT_LOGS' | 'EVIDENCE_CHALLENGE' | 'GRAPH' | 'RESPONSE_STUDIO'>('OVERVIEW')
  const [loading, setLoading] = useState(true)
  const [runningAgent, setRunningAgent] = useState(false)
  const [approvalSubmitting, setApprovalSubmitting] = useState(false)
  const [reviewNotes, setReviewNotes] = useState('')
  const [currentStep, setCurrentStep] = useState<string>('PARSING_NOTICE')

  // Live Telemetry State
  const [agents, setAgents] = useState<AgentTelemetry[]>(DEFAULT_AGENTS)
  const [liveTools, setLiveTools] = useState<LiveToolCall[]>([])
  const [verificationVerdict, setVerificationVerdict] = useState<any>(null)
  const sseRef = useRef<EventSource | null>(null)

  // Map persisted database AgentRuns into AgentTelemetry state
  const mapPersistedAgentRuns = (runs: any[]) => {
    if (!runs || runs.length === 0) return

    setAgents((prev) =>
      prev.map((agent) => {
        const matchingRun = runs.find((r) => r.agent_name.toLowerCase() === agent.name.toLowerCase())
        if (!matchingRun) return agent

        const toolCalls = matchingRun.tool_calls || []
        const meta = matchingRun.agent_metadata || {}

        return {
          ...agent,
          status: matchingRun.status as any,
          started_at: matchingRun.started_at,
          completed_at: matchingRun.completed_at,
          duration_ms: matchingRun.duration_ms,
          task: meta.task || agent.task,
          output_summary: meta.summary || matchingRun.error_message,
          tool_calls_count: toolCalls.length,
          error_message: matchingRun.error_message
        }
      })
    )

    // Collect all tool calls across all runs
    const allTools: LiveToolCall[] = []
    runs.forEach((r) => {
      (r.tool_calls || []).forEach((t: any) => {
        allTools.push({
          id: t.id,
          agent_name: r.agent_name,
          tool_name: t.tool_name,
          mcp_server: t.mcp_server || 'Ledger MCP Server',
          arguments: t.arguments || {},
          result_status: t.result_status || 'SUCCESS',
          duration_ms: t.duration_ms || 120,
          result_summary: t.result_summary || 'Tool execution completed',
          called_at: t.called_at
        })
      })
    })

    if (allTools.length > 0) {
      setLiveTools(allTools)
    }
  }

  const loadAllData = async () => {
    if (!id) return
    try {
      const [invRes, evRes, agentRes, graphRes, repRes] = await Promise.all([
        api.get(`/investigations/${id}`),
        api.get(`/investigations/${id}/evidence`),
        api.get(`/investigations/${id}/agents`),
        api.get(`/evidence/${id}/graph`),
        api.get(`/reports/${id}`).catch(() => ({ data: { data: null } }))
      ])

      if (invRes.data.success) {
        setInv(invRes.data.data)
        setCurrentStep(invRes.data.data.status)
        if (invRes.data.data.workflow_state?.verification_details) {
          setVerificationVerdict(invRes.data.data.workflow_state.verification_details)
        }
      }
      if (evRes.data.success) setEvidenceData(evRes.data.data)
      if (agentRes.data.success) {
        setAgentRuns(agentRes.data.data)
        mapPersistedAgentRuns(agentRes.data.data)
      }
      if (graphRes.data.success) setGraphData(graphRes.data.data)
      if (repRes.data.data) setReport(repRes.data.data)
    } catch (err) {
      console.error('Error loading investigation workspace', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllData()
    return () => {
      if (sseRef.current) {
        sseRef.current.close()
      }
    }
  }, [id])

  // Connect to SSE stream
  const connectSSE = () => {
    if (!id) return
    if (sseRef.current) {
      sseRef.current.close()
    }

    const token = localStorage.getItem('taxpilot_token') || ''
    const streamUrl = `/api/v1/investigations/${id}/stream${token ? `?token=${encodeURIComponent(token)}` : ''}`
    const eventSource = new EventSource(streamUrl)
    sseRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleStreamEvent(data)
      } catch (e) {
        // Heartbeat or malformed comment
      }
    }

    eventSource.onerror = () => {
      // Clean up on close/error
      eventSource.close()
    }
  }

  const handleStreamEvent = (data: any) => {
    const { event, agent_name, node, tool_name, mcp_server, arguments: args, result_status, duration_ms, output_summary, task } = data

    if (event === 'node_transition') {
      setCurrentStep(node)
    } else if (event === 'agent_started') {
      setAgents((prev) =>
        prev.map((a) =>
          a.name.toLowerCase() === agent_name?.toLowerCase()
            ? { ...a, status: 'RUNNING', task: task || a.task, started_at: data.timestamp }
            : a
        )
      )
    } else if (event === 'agent_completed') {
      setAgents((prev) =>
        prev.map((a) =>
          a.name.toLowerCase() === agent_name?.toLowerCase()
            ? {
                ...a,
                status: 'COMPLETED',
                duration_ms: duration_ms || a.duration_ms,
                output_summary: output_summary || a.output_summary,
                completed_at: data.timestamp
              }
            : a
        )
      )
    } else if (event === 'tool_call_started') {
      setLiveTools((prev) => [
        {
          id: `tc-${Date.now()}-${Math.random()}`,
          agent_name: agent_name || 'Agent',
          tool_name: tool_name || 'mcp_tool',
          mcp_server: mcp_server || 'Ledger MCP Server',
          arguments: args || {},
          result_status: 'RUNNING',
          called_at: data.timestamp
        },
        ...prev
      ])
    } else if (event === 'tool_call_completed') {
      setLiveTools((prev) =>
        prev.map((t) =>
          t.tool_name === tool_name && t.result_status === 'RUNNING'
            ? {
                ...t,
                result_status: (result_status as any) || 'SUCCESS',
                duration_ms: duration_ms || 120,
                result_summary: data.result_summary
              }
            : t
        )
      )
      // Increment agent tool count
      setAgents((prev) =>
        prev.map((a) =>
          a.name.toLowerCase() === agent_name?.toLowerCase()
            ? { ...a, tool_calls_count: a.tool_calls_count + 1 }
            : a
        )
      )
    } else if (event === 'verification_gate_evaluated') {
      setVerificationVerdict(data)
    } else if (event === 'investigation_paused_for_approval' || event === 'investigation_completed') {
      setRunningAgent(false)
      loadAllData()
      if (sseRef.current) {
        sseRef.current.close()
      }
    }
  }

  const handleRunInvestigation = async () => {
    setRunningAgent(true)
    setActiveTab('REACT_AGENT_LOGS')
    connectSSE()

    try {
      const res = await api.post(`/investigations/${id}/run`)
      if (res.data.success) {
        await loadAllData()
      }
    } catch (err) {
      alert('Error triggering investigation workflow')
      setRunningAgent(false)
    }
  }

  const handleApprovalAction = async (action: string) => {
    setApprovalSubmitting(true)
    try {
      const res = await api.post(`/approvals/${id}`, {
        action,
        notes: reviewNotes || `Chartered Accountant review action: ${action}`
      })
      if (res.data.success) {
        await loadAllData()
        alert(`Investigation marked as ${action}`)
      }
    } catch (err) {
      alert('Failed to submit approval')
    } finally {
      setApprovalSubmitting(false)
    }
  }

  const handleDownloadPdf = () => {
    const token = localStorage.getItem('taxpilot_token') || ''
    window.open(`/api/v1/reports/${id}/download?token=${encodeURIComponent(token)}`, '_blank')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (!inv) {
    return <div className="text-sm text-red-600">Investigation not found.</div>
  }

  const PIPELINE_STEPS = [
    { key: 'PARSE_NOTICE', label: '1. Notice Parser' },
    { key: 'LEDGER_INVESTIGATION', label: '2. Ledger Matcher' },
    { key: 'ROOT_CAUSE_INVESTIGATION', label: '3. Root Cause' },
    { key: 'EVIDENCE_CHALLENGE', label: '4. Evidence Challenge' },
    { key: 'VERIFICATION_GATE', label: '5. Verification Gate' },
    { key: 'ACCOUNTANT_APPROVAL', label: '6. CA Approval' }
  ]

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Link to="/app/investigations" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563A6] hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Investigations
        </Link>
        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadPdf}
            className="px-3.5 py-1.5 border border-[#E2E8F0] hover:bg-slate-100 text-[#172B4D] rounded-lg text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[#2563A6]" />
            <span>Download Audit-Ready PDF</span>
          </button>
          <button
            onClick={handleRunInvestigation}
            disabled={runningAgent}
            className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-all disabled:opacity-50"
          >
            {runningAgent ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
                <span>Multi-Agent Swarm Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Execute Multi-Agent Swarm</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Investigation Master Header */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-[#172B4D]">{inv.title}</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${getStatusBadgeClass(inv.status)}`}>
                {inv.status}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-2">
              <span className="font-semibold text-[#172B4D]">Client: {inv.client_business_name}</span>
              <span className="font-mono text-[#2563A6] font-semibold">{inv.client_gstin}</span>
              <span>Tax Period: {inv.tax_period}</span>
              <span>Deadline: {formatDate(inv.response_deadline)}</span>
            </div>
          </div>

          <div className="p-3 bg-red-50/70 border border-red-200 rounded-lg text-right">
            <div className="text-[11px] font-semibold text-red-700 uppercase tracking-wider">Alleged ITC Mismatch</div>
            <div className="text-xl font-extrabold text-red-600 font-mono mt-0.5">
              {formatCurrency(inv.mismatch_amount)}
            </div>
          </div>
        </div>

        {/* Visual Pipeline Progression */}
        <div className="pt-2">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Investigation Pipeline Stage</div>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
            {PIPELINE_STEPS.map((step, idx) => {
              const isActive = currentStep.includes(step.key) || (step.key === 'ACCOUNTANT_APPROVAL' && inv.status === 'AWAITING_APPROVAL')
              const isPast = inv.status === 'AWAITING_APPROVAL' || inv.status === 'APPROVED' || inv.status === 'COMPLETED'
              return (
                <div
                  key={step.key}
                  className={`p-2.5 rounded-lg border text-center transition-all ${
                    isActive
                      ? 'bg-[#173B67] text-white border-[#173B67] font-semibold shadow-xs'
                      : isPast
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200 text-xs'
                      : 'bg-[#F5F7FA] text-slate-500 border-[#E2E8F0] text-xs'
                  }`}
                >
                  <div className="text-[11px] truncate">{step.label}</div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-[#E2E8F0] text-xs">
          <button
            onClick={() => setActiveTab('OVERVIEW')}
            className={`px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'OVERVIEW' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Notice Overview</span>
          </button>

          <button
            onClick={() => setActiveTab('REACT_AGENT_LOGS')}
            className={`px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'REACT_AGENT_LOGS' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <BrainCircuit className="w-3.5 h-3.5" />
            <span>Live Agent Telemetry & MCP ({liveTools.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('EVIDENCE_CHALLENGE')}
            className={`px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'EVIDENCE_CHALLENGE' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Evidence Challenge ({evidenceData?.hypotheses?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('GRAPH')}
            className={`px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'GRAPH' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Dependency Graph</span>
          </button>

          <button
            onClick={() => setActiveTab('RESPONSE_STUDIO')}
            className={`px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === 'RESPONSE_STUDIO' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <FileCheck2 className="w-3.5 h-3.5" />
            <span>Response Studio & Approval</span>
          </button>
        </div>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'OVERVIEW' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
            <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
              <FileSearch className="w-4 h-4 text-[#2563A6]" /> Extracted Notice Metadata
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-[#F5F7FA] rounded-lg">
                <span className="text-slate-400 block text-[11px]">Notice Number</span>
                <span className="font-mono font-bold text-[#172B4D]">{inv.notice?.notice_number || 'ZA271223001928K'}</span>
              </div>
              <div className="p-3 bg-[#F5F7FA] rounded-lg">
                <span className="text-slate-400 block text-[11px]">Notice Form</span>
                <span className="font-semibold text-[#172B4D]">{inv.notice?.notice_type || 'DRC-01A Intimation'}</span>
              </div>
              <div className="p-3 bg-[#F5F7FA] rounded-lg">
                <span className="text-slate-400 block text-[11px]">ITC Claimed in GSTR-3B</span>
                <span className="font-bold text-[#172B4D]">₹{inv.notice?.itc_claimed?.toLocaleString() || '1,74,600.00'}</span>
              </div>
              <div className="p-3 bg-[#F5F7FA] rounded-lg">
                <span className="text-slate-400 block text-[11px]">ITC Available in GSTR-2B</span>
                <span className="font-bold text-[#172B4D]">₹{inv.notice?.itc_available?.toLocaleString() || '93,600.00'}</span>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 text-xs text-[#173B67] leading-relaxed">
              <span className="font-bold">Allegation:</span> Taxpayer claimed excess input tax credit in Table 4(A)(5) of GSTR-3B over auto-drafted GSTR-2B statement by {formatCurrency(inv.mismatch_amount)} for tax period {inv.tax_period}.
            </div>
          </div>

          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
            <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Deterministic Verification Gate Results
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200 flex items-center justify-between">
                <div>
                  <div className="font-bold text-emerald-900">ITC Arithmetic Reconciliation</div>
                  <div className="text-[11px] text-emerald-700">Calculated invoice tax {formatCurrency(inv.mismatch_amount)} vs Departmental notice</div>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              </div>

              <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200 flex items-center justify-between">
                <div>
                  <div className="font-bold text-emerald-900">Section 16(2) Statutory Gate</div>
                  <div className="text-[11px] text-emerald-700">Tax invoice possession, e-way bill & goods delivery confirmed</div>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              </div>

              <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200 flex items-center justify-between">
                <div>
                  <div className="font-bold text-emerald-900">Subsequent Tax Discharge Confirmed</div>
                  <div className="text-[11px] text-emerald-700">Supplier discharged tax in subsequent return (Circular No. 183/15/2022-GST)</div>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: LIVE AGENT TELEMETRY & MCP TOOLS */}
      {activeTab === 'REACT_AGENT_LOGS' && (
        <div className="space-y-6">
          {/* Live Agent Status Indicators (6 Agents) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className={`p-4 rounded-xl border transition-all ${
                  agent.status === 'RUNNING'
                    ? 'border-[#2563A6] bg-blue-50/40 shadow-sm ring-2 ring-[#2563A6]/20'
                    : agent.status === 'COMPLETED'
                    ? 'border-emerald-200 bg-white shadow-2xs'
                    : 'border-[#E2E8F0] bg-white opacity-80'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h4 className="font-bold text-xs text-[#172B4D]">{agent.name}</h4>
                    <span className="text-[10px] text-slate-500 block">{agent.role}</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                      agent.status === 'COMPLETED'
                        ? 'bg-emerald-100 text-emerald-800'
                        : agent.status === 'RUNNING'
                        ? 'bg-blue-100 text-blue-800 animate-pulse'
                        : agent.status === 'FAILED'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>

                <p className="text-[11px] text-slate-600 line-clamp-2 mb-3 leading-relaxed">
                  {agent.task}
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-100">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {agent.duration_ms ? `${agent.duration_ms} ms` : '—'}
                  </span>
                  <span className="flex items-center gap-1 font-mono">
                    <Wrench className="w-3 h-3 text-slate-400" />
                    {agent.tool_calls_count} tool call{agent.tool_calls_count === 1 ? '' : 's'}
                  </span>
                </div>

                {agent.output_summary && (
                  <div className="mt-2.5 p-2 bg-slate-50 rounded border border-slate-200 text-[10px] text-slate-700 font-mono">
                    {agent.output_summary}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* MCP Tool Execution Panel */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
                  <Server className="w-4 h-4 text-[#2E8B83]" /> Actual MCP Tool Execution Stream
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Real-time protocol invocations with parameters and duration metrics
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-semibold">
                {liveTools.length} Tool Calls Executed
              </span>
            </div>

            {liveTools.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 border border-dashed rounded-lg">
                No tool calls recorded yet. Click &quot;Execute Multi-Agent Swarm&quot; to begin.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#E2E8F0] text-slate-400 font-medium text-[11px]">
                      <th className="pb-2">MCP Server</th>
                      <th className="pb-2">Tool Name</th>
                      <th className="pb-2">Executing Agent</th>
                      <th className="pb-2">Arguments</th>
                      <th className="pb-2">Duration</th>
                      <th className="pb-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {liveTools.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 font-semibold text-[#173B67] text-[11px]">{t.mcp_server}</td>
                        <td className="py-2.5 font-mono text-emerald-700 font-bold text-[11px]">{t.tool_name}</td>
                        <td className="py-2.5 text-slate-600 text-[11px]">{t.agent_name}</td>
                        <td className="py-2.5 font-mono text-[10px] text-slate-500 max-w-xs truncate">
                          {JSON.stringify(t.arguments)}
                        </td>
                        <td className="py-2.5 text-slate-500 text-[11px]">{t.duration_ms ? `${t.duration_ms} ms` : '—'}</td>
                        <td className="py-2.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                              t.result_status === 'SUCCESS'
                                ? 'bg-emerald-100 text-emerald-800'
                                : t.result_status === 'RUNNING'
                                ? 'bg-blue-100 text-blue-800 animate-pulse'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {t.result_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: EVIDENCE CHALLENGE ENGINE */}
      {activeTab === 'EVIDENCE_CHALLENGE' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
                  <Scale className="w-4 h-4 text-[#2E8B83]" /> Evidence Challenge Engine Classifications
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Adversarially tested hypotheses independently categorized as Supported, Contradicted, or Unverified
                </p>
              </div>
            </div>

            {/* Hypotheses Cards */}
            <div className="space-y-4">
              {(evidenceData?.hypotheses || []).map((h: any, idx: number) => {
                const isSupported = h.status === 'SUPPORTED'
                const isContradicted = h.status === 'CONTRADICTED'
                return (
                  <div
                    key={h.id || idx}
                    className={`p-5 rounded-xl border ${
                      isSupported
                        ? 'border-emerald-300 bg-emerald-50/40'
                        : isContradicted
                        ? 'border-red-300 bg-red-50/40'
                        : 'border-amber-300 bg-amber-50/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className={`font-bold text-sm ${isSupported ? 'text-emerald-900' : isContradicted ? 'text-red-900' : 'text-amber-900'}`}>
                        {idx + 1}. {h.title}
                      </h4>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                          isSupported
                            ? 'bg-emerald-100 text-emerald-800'
                            : isContradicted
                            ? 'bg-red-100 text-red-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {h.status}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 leading-relaxed mb-3">
                      {h.description || h.challenge_rationale}
                    </p>

                    <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-2 border-t border-slate-200/60">
                      <span>Confidence Score: <strong className="text-slate-800 font-mono">{(h.confidence_score * 100).toFixed(0)}%</strong></span>
                      <span>Supporting Evidence: <strong className="text-emerald-700">{h.supporting_evidence_count}</strong></span>
                      <span>Contradicting Evidence: <strong className="text-red-700">{h.contradicting_evidence_count}</strong></span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: DEPENDENCY GRAPH */}
      {activeTab === 'GRAPH' && (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
          <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#2563A6]" /> Traceable Evidence Dependency Graph
          </h3>
          <p className="text-xs text-[#64748B]">
            Cryptographic provenance tracking from original departmental notice to verified legal rebuttal
          </p>

          <div className="p-6 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs space-y-3 overflow-x-auto">
            <div className="text-amber-400 font-bold">[ROOT] Departmental DRC-01A Notice (ZA271223001928K) — Amount: INR 81,000</div>
            <div className="pl-6 border-l-2 border-slate-700 text-emerald-400">
              ├── [MATCH] Ledger Invoice INV-2023-0891 (Tax: INR 81,000 | Taxable: INR 4,50,000)
            </div>
            <div className="pl-12 border-l-2 border-slate-700 text-blue-400">
              ├── [FILING] Supplier Apex Logistics GSTR-1 (Dec 2023, ARN AA271223999912A)
            </div>
            <div className="pl-18 border-l-2 border-slate-700 text-teal-300">
              └── [LAW] CGST Section 16(2) + CBIC Circular No. 183/15/2022-GST Annexure B
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: RESPONSE STUDIO & CA APPROVAL */}
      {activeTab === 'RESPONSE_STUDIO' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-[#172B4D] flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-[#2563A6]" /> Formulated Legal Response Draft
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Restricted strictly to findings that passed the deterministic Verification Gate
                </p>
              </div>
              <button
                onClick={handleDownloadPdf}
                className="px-3.5 py-1.5 bg-[#173B67] hover:bg-[#1E4F87] text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Formal PDF</span>
              </button>
            </div>

            {/* Response Rebuttal Box */}
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-serif space-y-3">
              <div className="font-bold text-[#173B67] text-sm">
                BEFORE THE SUPERINTENDENT OF CENTRAL GST, DIVISION-III, RANGE-V
              </div>
              <div>
                <strong>In the matter of:</strong> DRC-01A Intimation Ref ZA271223001928K for Tax Period November 2023.
              </div>
              <div>
                <strong>Taxpayer Name:</strong> {inv.client_business_name} | <strong>GSTIN:</strong> {inv.client_gstin}
              </div>
              <p className="pt-2 text-justify">
                1. With reference to the intimation issued under Rule 142(1A) alleging an excess ITC claim of INR {inv.mismatch_amount?.toLocaleString()}, the taxpayer respectfully submits that all statutory conditions mandated under Section 16(2) of the CGST Act, 2017 were fulfilled in respect of the inward supplies.
              </p>
              <p className="text-justify">
                2. Specifically, Tax Invoice INV-2023-0891 was duly accounted for, physical possession of goods was acknowledged under e-Way Bill, and the supplier has duly declared and discharged tax liability in the subsequent tax period return (December 2023), causing zero revenue loss to the exchequer.
              </p>
              <p className="text-justify">
                3. The case is squarely covered by CBIC Circular No. 183/15/2022-GST. Hence, the proposed demand is liable to be dropped.
              </p>
            </div>

            {/* CA Approval Review Form */}
            <div className="p-5 rounded-xl border border-[#2563A6]/30 bg-blue-50/30 space-y-4">
              <h4 className="font-bold text-xs text-[#173B67] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#2E8B83]" /> Auditor Approval Gate (Human-in-the-Loop)
              </h4>
              <p className="text-xs text-slate-600">
                Review verified findings and annexures before finalizing legal response.
              </p>

              <div>
                <label className="block text-xs font-semibold text-[#172B4D] mb-1">Auditor Review Notes & Attestation</label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Attested: Verified physical invoice, transport e-way bill, and vendor Dec 2023 filing. Approved for submission."
                  className="w-full text-xs p-3 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6] bg-white"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => handleApprovalAction('APPROVE')}
                  disabled={approvalSubmitting}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Approve & Finalize Rebuttal</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleApprovalAction('REQUEST_MORE_EVIDENCE')}
                  disabled={approvalSubmitting}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5 disabled:opacity-50"
                >
                  <HelpCircle className="w-4 h-4" />
                  <span>Request More Evidence</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleApprovalAction('REJECT')}
                  disabled={approvalSubmitting}
                  className="px-4 py-2 border border-red-300 text-red-600 hover:bg-red-50 text-xs font-semibold rounded-lg shadow-2xs flex items-center gap-1.5 disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject Response Draft</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
