import React, { useEffect, useState } from 'react'
import { api } from '@/services/api/client'
import { formatDate } from '@/utils'
import { Building2, ShieldCheck, Calendar } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'
import { EmptyState } from '@/components/ui/EmptyState'

export function AdminOrganizationPage() {
  const [orgs, setOrgs] = useState<any[]>([])
  const [clients, setClients] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadOrgData() {
      try {
        const [orgRes, clientRes] = await Promise.all([
          api.get('/users/organizations'),
          api.get('/clients')
        ])
        if (orgRes.data.success) setOrgs(orgRes.data.data)
        if (clientRes.data.success) setClients(clientRes.data.data)
      } catch (e) {
        console.error('Failed to load org data', e)
      } finally {
        setLoading(false)
      }
    }
    loadOrgData()
  }, [])

  return (
    <div className="space-y-6">
      <PageHeader
        badge={{ icon: <Building2 className="w-3.5 h-3.5" />, label: 'Multi-Tenant Tax Organization Directory' }}
        title="Organization & Entity Management"
        description="Manage multi-tenant accounting firm boundaries, client GSTIN profiles, and workspace allocations."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Registered Organizations */}
        <GlassCard className="p-6 space-y-4">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2">
            <Building2 className="w-4 h-4 text-brand-orange" />
            Registered Tenant Organizations
          </h3>

          {loading ? (
            <SkeletonLoader type="row" count={3} />
          ) : orgs.length === 0 ? (
            <EmptyState
              icon={<Building2 className="w-6 h-6" />}
              title="No organizations"
              description="No tenant organizations registered yet."
            />
          ) : (
            <div className="divide-y divide-white/5">
              {orgs.map((o) => (
                <div key={o.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-white">{o.name}</div>
                    <div className="text-[10px] text-text-muted font-mono mt-0.5">slug: {o.slug}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="inline-block px-2.5 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-[10px] font-bold text-accent-mint">
                      {o.plan || 'ENTERPRISE'}
                    </span>
                    <div className="text-[10px] text-text-muted mt-1 font-mono flex items-center justify-end gap-1">
                      <Calendar className="w-2.5 h-2.5" />
                      {formatDate(o.created_at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Managed Client Tax Entities */}
        <GlassCard className="p-6 space-y-4">
          <h3 className="font-semibold text-sm text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-accent-mint" />
            Managed Client Taxpayers
          </h3>

          {loading ? (
            <SkeletonLoader type="row" count={3} />
          ) : clients.length === 0 ? (
            <EmptyState
              icon={<ShieldCheck className="w-6 h-6" />}
              title="No clients"
              description="No client taxpayer entities configured yet."
            />
          ) : (
            <div className="divide-y divide-white/5">
              {clients.map((c) => (
                <div key={c.id} className="py-3.5 flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold text-white">{c.business_name}</div>
                    <div className="text-[10px] text-text-muted font-mono mt-0.5">
                      GSTIN: {c.primary_gstin}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="inline-block px-2.5 py-0.5 rounded-full bg-brand-amber/15 border border-brand-amber/30 text-[10px] font-bold text-brand-amber">
                      {c.industry || 'General Industry'}
                    </span>
                    <div className="text-[10px] text-text-muted mt-1">
                      State: {c.state_code || '27 (MH)'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
