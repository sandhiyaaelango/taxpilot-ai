import React, { useEffect, useState } from 'react'
import { api } from '@/services/api/client'
import { formatDate } from '@/utils'
import { History, User } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'
import { EmptyState } from '@/components/ui/EmptyState'

export function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadLogs() {
      try {
        const res = await api.get('/audit-logs')
        if (res.data.success) setLogs(res.data.data)
      } catch (e) {
        console.error('Failed to load audit logs', e)
      } finally {
        setLoading(false)
      }
    }
    loadLogs()
  }, [])

  const ACTION_COLORS: Record<string, string> = {
    UPLOAD: 'text-brand-amber bg-brand-amber/15 border-brand-amber/30',
    RUN: 'text-brand-orange bg-brand-orange/15 border-brand-orange/30',
    APPROVE: 'text-status-success bg-status-success/15 border-status-success/30',
    REJECT: 'text-status-error bg-status-error/15 border-status-error/30',
    EXPORT: 'text-accent-mint bg-accent-mint/15 border-accent-mint/30',
    LOGIN: 'text-text-secondary bg-surface-2 border-white/10',
    CREATE: 'text-accent-mint bg-accent-mint/15 border-accent-mint/30'
  }

  const getActionColor = (action: string) => {
    const key = Object.keys(ACTION_COLORS).find(k => action?.toUpperCase().includes(k))
    return key ? ACTION_COLORS[key] : 'text-text-secondary bg-surface-2 border-white/10'
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge={{ icon: <History className="w-3.5 h-3.5" />, label: 'Immutable Governance Ledger' }}
        title="Compliance Audit Trail"
        description="Immutable historical log of all notice uploads, agent runs, human approvals, and PDF exports."
      />

      <GlassCard className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonLoader type="row" count={8} />
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12">
            <EmptyState
              icon={<History className="w-8 h-8" />}
              title="No audit events"
              description="Audit log entries will appear here as the system is used."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-white/8 bg-surface-2">
                <tr>
                  {['Timestamp', 'User / Actor', 'Action', 'Resource Type', 'Details'].map((h) => (
                    <th key={h} className="px-5 py-3.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-surface-2/50 transition-colors">
                    <td className="px-5 py-3.5 text-[11px] text-text-muted font-mono whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-brand-orange/15 border border-brand-orange/25 flex items-center justify-center shrink-0">
                          <User className="w-3 h-3 text-brand-orange" />
                        </div>
                        <span className="text-xs text-white">{log.user_email}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span className={`font-mono font-bold text-[10px] px-2 py-0.5 rounded border ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-[11px] text-text-secondary">{log.resource_type}</td>
                    <td className="px-5 py-3.5 text-[10px] text-text-muted font-mono max-w-[200px] truncate">
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
