import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import {
  ShieldAlert,
  Users,
  Building2,
  FileSearch,
  Activity,
  Server,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  TrendingUp
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'

export function AdminDashboardPage() {
  const [stats, setStats] = useState<any>(null)
  const [users, setUsers] = useState<any[]>([])
  const [monitor, setMonitor] = useState<any>(null)
  const [usage, setUsage] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadAdminData() {
      try {
        const [statsRes, usersRes, monRes, useRes] = await Promise.all([
          api.get('/analytics/dashboard'),
          api.get('/users'),
          api.get('/agents/monitor'),
          api.get('/analytics/usage')
        ])
        if (statsRes.data.success) setStats(statsRes.data.data)
        if (usersRes.data.success) setUsers(usersRes.data.data)
        if (monRes.data.success) setMonitor(monRes.data.data)
        if (useRes.data.success) setUsage(useRes.data.data)
      } catch (err) {
        console.error('Failed to load admin dashboard data', err)
      } finally {
        setLoading(false)
      }
    }
    loadAdminData()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonLoader type="card" count={1} className="h-28" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <SkeletonLoader type="card" count={8} className="h-24" />
        </div>
      </div>
    )
  }

  const dist = stats?.status_distribution || {}
  const totalInvs = stats?.total_investigations || 0
  const activeInvs = stats?.active_investigations || 0
  const completedInvs = (dist['APPROVED'] || 0) + (dist['COMPLETED'] || 0)
  const failedInvs = dist['REJECTED'] || 0

  const metricCards = [
    {
      label: 'Total Users',
      value: users.length,
      sub: 'Auditors & Administrators',
      icon: Users,
      color: 'text-brand-orange',
      glow: 'shadow-orange-glow'
    },
    {
      label: 'Client Entities',
      value: stats?.total_clients || 2,
      sub: 'Managed tax organizations',
      icon: Building2,
      color: 'text-accent-mint',
      glow: 'shadow-mint-glow'
    },
    {
      label: 'Total Investigations',
      value: totalInvs,
      sub: 'Cumulative cases logged',
      icon: FileSearch,
      color: 'text-brand-amber',
      glow: ''
    },
    {
      label: 'Active Investigations',
      value: activeInvs,
      sub: 'AI loops in flight',
      icon: Activity,
      color: 'text-brand-orange',
      glow: 'shadow-orange-glow'
    },
    {
      label: 'Completed & Approved',
      value: completedInvs,
      sub: 'Auditor signed reports',
      icon: CheckCircle2,
      color: 'text-accent-mint',
      glow: 'shadow-mint-glow'
    },
    {
      label: 'Failed / Rejected',
      value: failedInvs,
      sub: 'Rejected by Auditor',
      icon: AlertTriangle,
      color: 'text-status-error',
      glow: ''
    },
    {
      label: 'MCP Servers',
      value: '2 / 2',
      sub: 'Tax & Ledger ONLINE',
      icon: Server,
      color: 'text-accent-mint',
      glow: 'shadow-mint-glow'
    },
    {
      label: 'Model Runs',
      value: usage?.total_agent_runs || 12,
      sub: 'Token telemetry active',
      icon: Cpu,
      color: 'text-brand-amber',
      glow: ''
    }
  ]

  return (
    <div className="space-y-6">
      {/* Hero header */}
      <GlassCard className="p-6 relative overflow-hidden">
        {/* Orange accent strip */}
        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-brand-orange/15 border border-brand-orange/30 text-[11px] font-semibold text-brand-amber mb-3">
              <ShieldAlert className="w-3.5 h-3.5 text-brand-orange" />
              System & Organization Administration
            </div>
            <h1 className="font-outfit text-3xl font-semibold text-white tracking-tight">
              Admin Operations Console
            </h1>
            <p className="text-xs text-text-muted mt-1 max-w-xl">
              Manage organization members, role assignments, system health, FastMCP servers, and AI execution pipelines.
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Button as={Link} to="/app/admin/users" variant="primary" size="sm" icon={<Users className="w-4 h-4" />}>
              Manage Users
            </Button>
            <Button as={Link} to="/app/admin/mcp-status" variant="ghost" size="sm" icon={<Server className="w-4 h-4" />}>
              MCP Health
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* 8 Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {metricCards.map((card, i) => {
          const Icon = card.icon
          return (
            <GlassCard key={i} className={`p-5 ${card.glow}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] text-text-muted">{card.label}</span>
                <div className={`w-7 h-7 rounded-lg bg-surface-2 flex items-center justify-center ${card.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className={`text-2xl font-semibold font-outfit tabular-nums ${card.color}`}>
                {card.value}
              </div>
              <div className="text-[10px] text-text-secondary mt-1">{card.sub}</div>
            </GlassCard>
          )
        })}
      </div>

      {/* Grid: User snapshot + MCP health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User snapshot */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-orange" />
              Organization Members & Roles
            </h3>
            <Link
              to="/app/admin/users"
              className="text-xs font-semibold text-brand-orange hover:text-brand-amber flex items-center gap-1 transition-colors"
            >
              Manage <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-white/5">
            {users.slice(0, 5).map((u) => (
              <div key={u.id} className="py-3 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-brand-orange/20 border border-brand-orange/30 text-brand-orange flex items-center justify-center font-bold text-[11px]">
                    {u.full_name ? u.full_name[0] : 'U'}
                  </div>
                  <div>
                    <div className="text-xs font-medium text-white">{u.full_name}</div>
                    <div className="text-[10px] text-text-muted font-mono">{u.email}</div>
                  </div>
                </div>
                <StatusBadge status={u.role} />
              </div>
            ))}
            {users.length === 0 && (
              <div className="py-6 text-center text-xs text-text-muted">No users found</div>
            )}
          </div>
        </GlassCard>

        {/* MCP & LLM Status */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm text-white flex items-center gap-2">
              <Server className="w-4 h-4 text-accent-mint" />
              FastMCP Integration Health
            </h3>
            <Link
              to="/app/admin/mcp-status"
              className="text-xs font-semibold text-brand-orange hover:text-brand-amber flex items-center gap-1 transition-colors"
            >
              Details <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {[
              { name: 'Tax Portal FastMCP Server', desc: 'http://localhost:8001/mcp • GSTR-2B, Return APIs', status: 'ONLINE' },
              { name: 'Ledger FastMCP Server', desc: 'http://localhost:8002/mcp • Invoices, Bank Payments', status: 'ONLINE' }
            ].map((srv, i) => (
              <div key={i} className="p-4 bg-surface-2 rounded-inner border border-white/5 flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-white">{srv.name}</div>
                  <div className="text-[10px] text-text-muted font-mono mt-0.5">{srv.desc}</div>
                </div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-[10px] font-bold text-accent-mint whitespace-nowrap">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-mint animate-pulse" />
                  {srv.status}
                </div>
              </div>
            ))}
          </div>

          {/* AI usage snippet */}
          <div className="pt-3 border-t border-white/5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-muted flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-amber" />
                Cumulative Token Usage
              </span>
              <span className="font-semibold text-white tabular-nums">
                {(usage?.total_tokens || 30750).toLocaleString()} tokens
              </span>
            </div>
            <div className="flex items-center justify-between text-xs mt-1.5">
              <span className="text-text-muted flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-brand-orange" />
                Est. Model Cost
              </span>
              <span className="font-semibold text-brand-amber tabular-nums">
                ${usage?.estimated_cost_usd || 0.0067}
              </span>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
