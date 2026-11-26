import React from 'react'
import { useAuthStore } from '@/stores/authStore'
import { Shield, Lock } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'

export function AdminProfilePage() {
  const { user, clearAuth } = useAuthStore()

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        badge={{ icon: <Shield className="w-3.5 h-3.5" />, label: 'Platform Superuser' }}
        title="System Administrator Profile"
        description="Root administrator identity, tenant administration authority, and security controls."
      />

      <GlassCard className="p-6 space-y-6">
        {/* Avatar row */}
        <div className="flex items-center gap-4 pb-6 border-b border-white/8">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-brand-orange/60 to-brand-amber/40 border border-brand-orange/40 text-white flex items-center justify-center font-bold text-xl shadow-orange-glow">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'A'}
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">{user?.full_name || 'System Administrator'}</h2>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-brand-orange/20 border border-brand-orange/35 text-brand-orange">
                ROLE: ADMIN
              </span>
              <span className="text-[11px] text-text-muted font-mono">{user?.email}</span>
            </div>
          </div>
        </div>

        {/* Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Administrator Name</label>
            <Input
              type="text"
              disabled
              value={user?.full_name || 'Admin User'}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Admin Email</label>
            <Input
              type="text"
              disabled
              value={user?.email || 'admin@abctraders.demo'}
              className="font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Administrative Scope</label>
            <Input
              type="text"
              disabled
              value="User Management, Org Boundary Governance, MCP & Telemetry"
              className="text-brand-amber"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">Investigation Sign-off Privilege</label>
            <Input
              type="text"
              disabled
              value="Restricted to AUDITOR Role (Separation of Duties)"
              className="text-status-warning"
            />
          </div>
        </div>

        {/* Separation of duties notice */}
        <div className="p-4 bg-status-warning/8 border border-status-warning/25 rounded-inner flex items-start gap-3">
          <Lock className="w-4 h-4 text-status-warning shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-semibold text-status-warning mb-1">Enforced Separation of Duties</div>
            <p className="text-[11px] text-text-muted leading-relaxed">
              Administrators maintain operational oversight, manage user credentials, and configure infrastructure,
              but cannot sign off or approve GST audit investigations on behalf of certified Auditors.
            </p>
          </div>
        </div>

        {/* Sign out */}
        <div className="flex justify-end pt-2 border-t border-white/5">
          <button
            onClick={clearAuth}
            className="px-4 py-2 rounded-nav text-xs font-semibold text-status-error
              bg-status-error/10 border border-status-error/25 hover:bg-status-error/20 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </GlassCard>
    </div>
  )
}
