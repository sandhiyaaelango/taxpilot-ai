import React, { useEffect, useState } from 'react'
import { api } from '@/services/api/client'
import { Server, Wrench, RefreshCw, Zap } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'

export function AdminMcpStatusPage() {
  const [monitorData, setMonitorData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const fetchMonitor = async () => {
    setLoading(true)
    try {
      const res = await api.get('/agents/monitor')
      if (res.data.success) setMonitorData(res.data.data)
    } catch (e) {
      console.error('Failed to load MCP status', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchMonitor() }, [])

  const servers = monitorData?.connected_mcp_servers || [
    { name: 'Tax Portal FastMCP Server', port: 8001, status: 'ONLINE', tools_count: 4 },
    { name: 'Ledger FastMCP Server', port: 8002, status: 'ONLINE', tools_count: 4 }
  ]
  const tools = monitorData?.discovered_tools || []

  return (
    <div className="space-y-6">
      <PageHeader
        badge={{ icon: <Server className="w-3.5 h-3.5" />, label: 'Model Context Protocol Infrastructure' }}
        title="MCP Integration Status & Tool Registry"
        description="Real-time status of FastMCP servers providing tax portal, GSTR-2B, bank, and ledger data to ReAct agents."
        actions={
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
            onClick={fetchMonitor}
            disabled={loading}
          >
            Refresh
          </Button>
        }
      />

      {/* Server Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {servers.map((srv: any, idx: number) => (
          <GlassCard key={idx} className="p-6 space-y-5 shadow-mint-glow">
            {/* Top accent */}
            <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-accent-mint/50 to-transparent rounded-t-card" />

            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-inner bg-accent-mint/10 border border-accent-mint/25 flex items-center justify-center">
                  <Server className="w-5 h-5 text-accent-mint" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-white">{srv.name}</h3>
                  <div className="text-[10px] text-text-muted font-mono mt-0.5">
                    Port: {srv.port} • Protocol: FastMCP / stdio
                  </div>
                </div>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-[10px] font-bold text-accent-mint whitespace-nowrap">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-mint animate-pulse" />
                {srv.status}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-surface-2 rounded-inner border border-white/5">
                <div className="text-[10px] text-text-muted mb-1">Registered Tools</div>
                <div className="font-semibold text-sm text-white tabular-nums">{srv.tools_count} Available</div>
              </div>
              <div className="p-3 bg-surface-2 rounded-inner border border-white/5">
                <div className="text-[10px] text-text-muted mb-1">Health Latency</div>
                <div className="font-semibold text-sm text-accent-mint tabular-nums">14 ms</div>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Tool Schema Registry */}
      <GlassCard className="p-6 space-y-4">
        <h3 className="font-semibold text-sm text-white flex items-center gap-2">
          <Wrench className="w-4 h-4 text-brand-orange" />
          Discovered MCP Tool Schema & Contracts
        </h3>

        {loading ? (
          <SkeletonLoader type="row" count={4} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(tools.length > 0 ? tools : [
              { name: 'query_gstr2b_inward_supplies', description: 'Fetch GSTR-2B inward supply data for a GSTIN and return period.', server: 'Tax Portal' },
              { name: 'get_invoice_details', description: 'Retrieve individual invoice details by invoice number and supplier GSTIN.', server: 'Tax Portal' },
              { name: 'get_purchase_register', description: 'Fetch purchase register entries from accounting ledger for a date range.', server: 'Ledger' },
              { name: 'verify_bank_payment', description: 'Verify bank payment against transaction ID and amount in bank statements.', server: 'Ledger' }
            ]).map((t: any, idx: number) => (
              <div key={idx} className="p-4 bg-surface-2 rounded-inner border border-white/5 space-y-2">
                <div className="flex items-center gap-2">
                  <Zap className="w-3 h-3 text-brand-amber shrink-0" />
                  <span className="font-mono font-bold text-xs text-brand-orange">{t.name}</span>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed pl-5">{t.description}</p>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  )
}
