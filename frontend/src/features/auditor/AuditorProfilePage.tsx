import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Shield, LogOut } from 'lucide-react'
import {
  GlassCard,
  Avatar,
  StatusBadge,
  Input,
  Button,
  PageHeader,
} from '@/components/ui'

export function AuditorProfilePage() {
  const navigate = useNavigate()
  const { user, clearAuth } = useAuthStore()

  const handleSignOut = () => {
    clearAuth()
    navigate('/auth/login')
  }

  return (
    <div className="space-y-5 max-w-4xl">
      <PageHeader
        title="Profile"
        subtitle="Authorized Auditor identity, statutory sign-off authority, and workspace preferences."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'Profile' },
        ]}
        actions={
          <Button
            variant="destructive"
            onClick={handleSignOut}
            leftIcon={<LogOut className="w-4 h-4" />}
          >
            Sign out
          </Button>
        }
      />

      <GlassCard className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border-subtle">
          <div className="flex items-center gap-4">
            <Avatar name={user?.full_name || user?.email} size="lg" />
            <div>
              <h2 className="text-[20px] font-semibold text-txt-primary">
                {user?.full_name || 'Chartered Accountant'}
              </h2>
              <div className="flex flex-wrap items-center gap-2.5 mt-1">
                <StatusBadge status="AUDITOR" />
                <span className="text-[13px] font-mono text-txt-muted">
                  {user?.email || 'ca@abctraders.demo'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Full Name"
            disabled
            value={user?.full_name || 'Chartered Accountant'}
          />
          <Input
            label="Work Email"
            disabled
            value={user?.email || 'ca@abctraders.demo'}
            className="font-mono"
          />
          <Input
            label="Statutory Authority"
            disabled
            value="Full Sign-Off & PDF Export (CGST Rule 142)"
          />
          <Input
            label="Organization ID"
            disabled
            value={user?.organization_id || 'Primary CA Firm'}
            className="font-mono"
          />
        </div>

        <div className="p-4 rounded-inner bg-accent-mint/[0.06] border border-accent-mint/25 flex items-start gap-3">
          <Shield className="w-5 h-5 text-accent-mint shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-[14px] font-medium text-txt-primary">
              Auditor Final Approval Authority
            </div>
            <p className="text-[13px] leading-[20px] text-txt-secondary">
              Your account is authorized to launch AI investigations, inspect evidence provenance,
              edit statutory reply drafts, and issue final signed PDF reports.
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
