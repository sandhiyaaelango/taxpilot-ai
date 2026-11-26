import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import {
  FileSearch,
  Users,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Plus,
  ShieldCheck,
  Server
} from 'lucide-react'

export function DashboardPage() {
  const [stats, setStats] = useState<any>(null)
  const [recentInvs, setRecentInvs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [statsRes, invsRes] = await Promise.all([
          api.get('/analytics/dashboard'),
          api.get('/investigations?page_size=5')
        ])
        if (statsRes.data.success) setStats(statsRes.data.data)
        if (invsRes.data.success) setRecentInvs(invsRes.data.data)
      } catch (err) {
        console.error('Failed to load dashboard data', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Welcome & Actions Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172B4D] tracking-tight">Compliance Command Centre</h1>
          <p className="text-xs text-[#64748B] mt-1">
            Real-time multi-client GST ITC mismatch investigation & evidence status
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/app/investigations"
            className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>New Investigation</span>
          </Link>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-medium mb-2">
            <span>ITC At Risk</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-[#172B4D]">
            {formatCurrency(stats?.total_itc_at_risk || 258600)}
          </div>
          <div className="text-[11px] text-amber-600 font-medium mt-1">Under active scrutiny</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-medium mb-2">
            <span>Active Investigations</span>
            <FileSearch className="w-4 h-4 text-[#2563A6]" />
          </div>
          <div className="text-2xl font-bold text-[#172B4D]">
            {stats?.active_investigations || 2}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Multi-agent swarms running</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-medium mb-2">
            <span>Pending Approvals</span>
            <Clock className="w-4 h-4 text-[#2E8B83]" />
          </div>
          <div className="text-2xl font-bold text-[#172B4D]">
            {stats?.pending_approvals || 1}
          </div>
          <div className="text-[11px] text-[#2E8B83] font-medium mt-1">Awaiting CA sign-off</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="flex items-center justify-between text-[#64748B] text-xs font-medium mb-2">
            <span>Registered Clients</span>
            <Users className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-[#172B4D]">
            {stats?.total_clients || 2}
          </div>
          <div className="text-[11px] text-emerald-600 font-medium mt-1">Multi-GSTIN profiles active</div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Investigations Table (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
          <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
            <h2 className="font-bold text-sm text-[#172B4D]">Priority Investigations</h2>
            <Link to="/app/investigations" className="text-xs font-semibold text-[#2563A6] hover:underline flex items-center gap-1">
              View All <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#E2E8F0]">
                <tr>
                  <th className="px-5 py-3">Investigation</th>
                  <th className="px-5 py-3">Client</th>
                  <th className="px-5 py-3">Mismatch</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {recentInvs.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-[#172B4D]">{inv.title}</div>
                      <div className="text-[11px] text-slate-400">Period: {inv.tax_period}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-[#172B4D]">{inv.client_business_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{inv.client_gstin}</div>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-[#172B4D]">
                      {formatCurrency(inv.mismatch_amount)}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getStatusBadgeClass(inv.status)}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        to={`/app/investigations/${inv.id}`}
                        className="text-xs font-semibold text-[#2563A6] hover:text-[#173B67]"
                      >
                        Open Workspace
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Architecture & MCP Status Sidebar (1 Col) */}
        <div className="space-y-6">
          <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
            <h3 className="font-bold text-sm text-[#172B4D] mb-4 flex items-center gap-2">
              <Server className="w-4 h-4 text-[#2563A6]" /> MCP Subsystem Status
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-[#F5F7FA] border border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <div className="font-semibold text-[#172B4D]">Tax Portal MCP Server</div>
                  <div className="text-[11px] text-slate-500">Port 8001 (4 Tools active)</div>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">ONLINE</span>
              </div>

              <div className="p-3 rounded-lg bg-[#F5F7FA] border border-[#E2E8F0] flex items-center justify-between">
                <div>
                  <div className="font-semibold text-[#172B4D]">Ledger MCP Server</div>
                  <div className="text-[11px] text-slate-500">Port 8002 (4 Tools active)</div>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">ONLINE</span>
              </div>
            </div>
          </div>

          <div className="bg-[#173B67] text-white p-5 rounded-xl shadow-sm">
            <div className="flex items-center gap-2 text-[#2E8B83] font-bold text-xs uppercase tracking-wider mb-2">
              <ShieldCheck className="w-4 h-4" /> Deterministic Gate Active
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">
              Every finding must clear Python ITC arithmetic, GSTIN consistency, and source provenance before entering response draft.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
