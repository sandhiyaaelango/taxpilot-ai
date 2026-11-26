import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/services/api/client'
import {
  Building2,
  Mail,
  Lock,
  User as UserIcon,
  ArrowRight,
  Eye,
  EyeOff,
  ShieldCheck,
  AlertCircle,
  FileSearch
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function RegisterPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [fullName, setFullName] = useState('')
  const [orgName, setOrgName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await api.post('/auth/register', {
        full_name: fullName,
        organization_name: orgName,
        email,
        password,
        role: 'OWNER'
      })
      if (res.data.success) {
        setAuth(res.data.data.user, res.data.data.access_token)
        navigate('/app/dashboard')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-bg-base text-white flex items-center justify-center p-6 relative overflow-hidden">
      {/* Ambient glows */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-32 left-1/4 w-[520px] h-[520px] rounded-full bg-brand-orange/8 blur-[140px]" />
        <div className="absolute bottom-0 right-1/4 w-[440px] h-[440px] rounded-full bg-brand-amber/5 blur-[140px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] rounded-full bg-brand-orange/4 blur-[100px]" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-orange/80 to-brand-amber/60 border border-brand-orange/40 flex items-center justify-center shadow-orange-glow">
              <FileSearch className="w-7 h-7 text-white" />
            </div>
            <span className="font-outfit font-semibold text-xl text-white tracking-tight">
              TaxPilot <span className="text-brand-orange">AI</span>
            </span>
          </Link>
          <p className="text-xs text-text-muted mt-2">
            Provision a dedicated GST compliance &amp; audit workspace for your firm.
          </p>
        </div>

        {/* Card */}
        <div className="rounded-card bg-surface-1 border border-white/8 shadow-glass backdrop-blur-xl p-7 sm:p-8 relative overflow-hidden">
          {/* Top glow strip */}
          <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-brand-orange/60 to-transparent" />

          <div className="flex items-center justify-between mb-6">
            <h1 className="text-lg font-semibold text-white">Create Firm Account</h1>
            <ShieldCheck className="w-5 h-5 text-brand-amber" />
          </div>

          {error && (
            <div className="mb-5 p-3.5 rounded-inner bg-status-error/12 border border-status-error/30 text-xs text-status-error flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            {/* Full name */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Chartered Accountant / Full Name
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-text-muted absolute left-3.5 top-3 pointer-events-none" />
                <Input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="CA Rajesh Sharma"
                  className="pl-10"
                />
              </div>
            </div>

            {/* Org name */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                CA Firm / Business Name
              </label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-text-muted absolute left-3.5 top-3 pointer-events-none" />
                <Input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Sharma & Associates LLP"
                  className="pl-10"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Official Work Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-text-muted absolute left-3.5 top-3 pointer-events-none" />
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="partner@sharma-ca.in"
                  className="pl-10"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Password (Min. 8 characters)
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-text-muted absolute left-3.5 top-3 pointer-events-none" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3 top-2.5 p-1 text-text-muted hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              fullWidth
              loading={loading}
              className="mt-2"
              icon={!loading ? <ArrowRight className="w-4 h-4" /> : undefined}
              iconPosition="right"
            >
              {loading ? 'Creating Account…' : 'Create Organization Workspace'}
            </Button>
          </form>

          <div className="mt-6 text-center text-xs text-text-muted">
            Already registered?{' '}
            <Link to="/auth/login" className="text-brand-orange font-semibold hover:text-brand-amber transition-colors">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
