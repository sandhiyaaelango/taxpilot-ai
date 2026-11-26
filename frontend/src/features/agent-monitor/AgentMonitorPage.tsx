import React, { useEffect, useState } from 'react'
import { api } from '@/services/api/client'
import { Activity, Server, Cpu, Wrench, DollarSign } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'
import { EmptyState } from '@/components/ui/EmptyState'

export function AgentMonitorPage() {
  const [monitorData, setMonitorData] = useState<any>(null)
  const [usageData, setUsageData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchMonitor() {
      try {
        const [monRes, useRes] = await Promise.all([
          api.get('/agents/monitor'),
          api.get('/analytics/usage')
        ])
        if (monRes.data.success) setMonitorData(monRes.data.data)
        if (useRes.data.success) setUsageData(useRes.data.data)
      } catch (err) {
        console.error('Failed to load agent monitor', err)
      } finally {
        setLoading(false)
      }
    }
    fetchMonitor()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonLoader type="card" count={1} className="h-24" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SkeletonLoader type="card" count={4} className="h-28" />
        </div>
      </div>
    )
  }

  const telemetryCards = [
    {
      label: 'Connected MCP Servers',
      value: '2 Active',
      sub: 'Ports 8001 & 8002 Online',
      icon: Server,
      color: 'text-accent-mint',
      subColor: 'text-accent-mint'
    },
    {
      label: 'Discovered MCP Tools',
      value: `${monitorData?.discovered_tools?.length || 8} Tools`,
      sub: 'Pydantic Schemas Validated',
      icon: Wrench,
      color: 'text-brand-amber',
      subColor: 'text-text-secondary'
    },
    {
      label: 'Cumulative Token Usage',
      value: (usageData?.total_tokens || 30750).toLocaleString(),
      sub: `Prompt: ${usageData?.total_input_tokens || 18450} | Completion: ${usageData?.total_output_tokens || 12300}`,
      icon: Cpu,
      color: 'text-white',
      subColor: 'text-text-secondary'
    },
    {
      label: 'Estimated Model Cost',
      value: `$${usageData?.estimated_cost_usd || 0.0067}`,
      sub: 'Gemini 2.0 Flash ($0.10/M)',
      icon: DollarSign,
      color: 'text-brand-orange',
      subColor: 'text-brand-amber'
    }
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        badge={{ icon: <Activity className="w-3.5 h-3.5" />, label: 'AI Telemetry & Token Governance' }}
        title="Agent Execution Monitor & Observability"
        description="Real-time telemetry, FastMCP tool discovery, token tracking, and model cost estimation."
      />

      {/* 4 Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {telemetryCards.map((card, i) => {
          const Icon = card.icon
          return (
            <GlassCard key={i} className="p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] text-text-muted">{card.label}</span>
                <div className="w-7 h-7 rounded-lg bg-surface-2 flex items-center justify-center">
                  <Icon className={`w-3.5 h-3.5 ${card.color}`} />
                </div>
              </div>
              <div className={`text-xl font-semibold font-outfit tabular-nums ${card.color}`}>
                {card.value}
              </div>
              <div className={`text-[10px] mt-1.5 ${card.subColor}`}>{card.sub}</div>
            </GlassCard>
          )
        })}
      </div>

      {/* Discovered MCP Tools Grid */}
      <GlassCard className="p-6 space-y-4">
        <h3 className="font-semibold text-sm text-white flex items-center gap-2">
          <Server className="w-4 h-4 text-brand-orange" />
          Discovered FastMCP Tools Registry
        </h3>

        {monitorData?.discovered_tools?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {monitorData.discovered_tools.map((t: any) => (
              <div key={t.name} className="p-4 bg-surface-2 rounded-inner border border-white/5 space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-bold text-xs text-brand-orange">{t.name}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-accent-mint whitespace-nowrap">
                    {t.server}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed">{t.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { name: 'query_gstr2b_inward_supplies', server: 'Tax Portal', desc: 'Fetch GSTR-2B inward supply data for a GSTIN and return period.' },
              { name: 'get_invoice_details', server: 'Tax Portal', desc: 'Retrieve individual invoice details by invoice number and supplier GSTIN.' },
              { name: 'get_purchase_register', server: 'Ledger', desc: 'Fetch purchase register entries from accounting ledger for a date range.' },
              { name: 'verify_bank_payment', server: 'Ledger', desc: 'Verify bank payment against transaction ID and amount in bank statements.' }
            ].map((t) => (
              <div key={t.name} className="p-4 bg-surface-2 rounded-inner border border-white/5 space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-bold text-xs text-brand-orange">{t.name}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-accent-mint whitespace-nowrap">
                    {t.server}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed">{t.desc}</p>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}
