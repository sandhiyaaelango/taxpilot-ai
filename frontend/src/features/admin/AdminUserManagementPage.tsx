import React, { useEffect, useState } from 'react'
import { api } from '@/services/api/client'
import { formatDate } from '@/utils'
import { Users, UserPlus, CheckCircle2, X, Shield } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { PageHeader } from '@/components/ui/PageHeader'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'
import { EmptyState } from '@/components/ui/EmptyState'

export function AdminUserManagementPage() {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Form state
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('TaxPilot@2024')
  const [role, setRole] = useState<'AUDITOR' | 'ADMIN'>('AUDITOR')

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users')
      if (res.data.success) setUsers(res.data.data)
    } catch (err) {
      console.error('Failed to load users', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchUsers() }, [])

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    setSuccess(null)
    try {
      const res = await api.post('/users', { email, full_name: fullName, password, role })
      if (res.data.success) {
        setSuccess(`User ${email} created as ${role}`)
        setModalOpen(false)
        setEmail('')
        setFullName('')
        fetchUsers()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create user')
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggleStatus = async (user: any) => {
    try {
      await api.patch(`/users/${user.id}`, { is_active: !user.is_active })
      fetchUsers()
    } catch (err) {
      console.error('Failed to toggle status', err)
    }
  }

  const handleChangeRole = async (user: any, newRole: string) => {
    try {
      await api.patch(`/users/${user.id}`, { role: newRole })
      fetchUsers()
    } catch (err) {
      console.error('Failed to change role', err)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        badge={{ icon: <Users className="w-3.5 h-3.5" />, label: 'Enterprise Identity & Access Management' }}
        title="User & Role Management"
        description="Provision and assign permissions exclusively for AUDITOR and ADMIN roles."
        actions={
          <Button
            variant="primary"
            size="sm"
            icon={<UserPlus className="w-4 h-4" />}
            onClick={() => setModalOpen(true)}
          >
            Provision New User
          </Button>
        }
      />

      {success && (
        <div className="p-3.5 rounded-inner bg-status-success/15 border border-status-success/30 text-xs text-status-success flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <GlassCard className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonLoader type="row" count={5} />
          </div>
        ) : users.length === 0 ? (
          <div className="p-12">
            <EmptyState icon={<Users className="w-8 h-8" />} title="No users found" description="Provision the first team member to get started." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-white/8 bg-surface-2">
                <tr>
                  {['User / Full Name', 'Work Email', 'Assigned Role', 'Account Status', 'Created Date', 'Actions'].map((h, i) => (
                    <th
                      key={h}
                      className={`px-5 py-3.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider ${i === 5 ? 'text-right' : ''}`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-surface-2/50 transition-colors group">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-brand-orange/20 border border-brand-orange/30 text-brand-orange flex items-center justify-center font-bold text-[11px] shrink-0">
                          {u.full_name ? u.full_name[0] : 'U'}
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-white">{u.full_name}</div>
                          <div className="text-[10px] text-text-muted font-mono">ID: {u.id.slice(0, 8)}…</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-xs text-text-secondary font-mono">{u.email}</td>
                    <td className="px-5 py-4">
                      <select
                        value={u.role}
                        onChange={(e) => handleChangeRole(u, e.target.value)}
                        className="text-[10px] font-bold px-2.5 py-1 rounded-full border cursor-pointer
                          bg-surface-2 border-white/10 text-white
                          focus:outline-none focus:ring-1 focus:ring-brand-orange/50"
                      >
                        <option value="AUDITOR">AUDITOR</option>
                        <option value="ADMIN">ADMIN</option>
                      </select>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        u.is_active
                          ? 'bg-status-success/15 border border-status-success/30 text-status-success'
                          : 'bg-status-error/15 border border-status-error/30 text-status-error'
                      }`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-status-success animate-pulse' : 'bg-status-error'}`} />
                        {u.is_active ? 'ACTIVE' : 'DISABLED'}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-[11px] text-text-muted font-mono">{formatDate(u.created_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => handleToggleStatus(u)}
                        className={`px-3 py-1 rounded-nav text-[11px] font-semibold transition-colors ${
                          u.is_active
                            ? 'bg-status-error/15 text-status-error hover:bg-status-error/25 border border-status-error/25'
                            : 'bg-status-success/15 text-status-success hover:bg-status-success/25 border border-status-success/25'
                        }`}
                      >
                        {u.is_active ? 'Disable' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Modal: Provision User */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <GlassCard className="max-w-md w-full p-6 space-y-5 shadow-orange-glow">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm text-white flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-brand-orange" />
                Provision New Team Member
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="w-7 h-7 rounded-full bg-surface-2 hover:bg-surface-3 flex items-center justify-center text-text-muted hover:text-white transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {error && (
              <div className="p-3 bg-status-error/15 border border-status-error/30 text-status-error text-xs rounded-inner">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Full Legal Name *</label>
                <Input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Meera Iyer"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Work Email Address *</label>
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. auditor@abctraders.demo"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Temporary Password *</label>
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">Assign System Role *</label>
                <select
                  value={role}
                  onChange={(e: any) => setRole(e.target.value)}
                  className="w-full px-3 py-2.5 bg-surface-2 border border-white/10 rounded-inner text-xs text-white
                    focus:outline-none focus:ring-2 focus:ring-brand-orange/50 focus:border-brand-orange/50"
                >
                  <option value="AUDITOR">AUDITOR – Reviews, edits & approves investigations</option>
                  <option value="ADMIN">ADMIN – System administration & user management</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" size="sm" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" loading={submitting}>
                  {submitting ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </form>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
