import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/services/api/client'
import { DEMO_CREDENTIALS } from '@/constants'
import {
  Lock,
  Mail,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  ArrowUpRight,
} from 'lucide-react'
import { Button, GlassCard, Input, StatusBadge } from '@/components/ui'

const REMEMBERED_EMAIL_KEY = 'taxpilot_remembered_email'

export function LoginPage() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [emailError, setEmailError] = useState('')
  const [passwordError, setPasswordError] = useState('')

  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBERED_EMAIL_KEY)
      if (saved) {
        setEmail(saved)
        setRememberMe(true)
      }
    } catch {
      // Ignore storage errors
    }
  }, [])

  const validate = () => {
    let valid = true
    setEmailError('')
    setPasswordError('')

    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setEmailError('Enter a valid work email address.')
      valid = false
    }
    if (!password) {
      setPasswordError('Enter your password.')
      valid = false
    }
    return valid
  }

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setError('')
    if (!validate()) return

    setLoading(true)
    try {
      const res = await api.post('/auth/login', { email: email.trim(), password })
      if (res.data.success) {
        try {
          if (rememberMe) {
            localStorage.setItem(REMEMBERED_EMAIL_KEY, email.trim())
          } else {
            localStorage.removeItem(REMEMBERED_EMAIL_KEY)
          }
        } catch {
          // Ignore storage errors
        }
        const loggedInUser = res.data.data.user
        setAuth(loggedInUser, res.data.data.access_token)
        const role = (loggedInUser?.role || '').toUpperCase()
        navigate(
          role === 'ADMIN' || role === 'OWNER'
            ? '/app/admin/dashboard'
            : '/app/auditor/dashboard'
        )
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Invalid email or password. Please verify your credentials.'
      )
    } finally {
      setLoading(false)
    }
  }

  const fillAuditorDemo = () => {
    setEmail('ca@abctraders.demo')
    setPassword(DEMO_CREDENTIALS.password)
    setError('')
    setEmailError('')
    setPasswordError('')
  }

  const fillAdminDemo = () => {
    setEmail(DEMO_CREDENTIALS.email)
    setPassword(DEMO_CREDENTIALS.password)
    setError('')
    setEmailError('')
    setPasswordError('')
  }

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row relative">
      {/* Left 55%: Brand Narrative & Floating Glass Reconciliation Card Stack */}
      <div className="relative lg:w-[55%] flex flex-col justify-between p-6 sm:p-10 lg:p-14 xl:p-16 border-b lg:border-b-0 lg:border-r border-border-subtle">
        {/* Top Mint Logo */}
        <div className="flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-nav bg-accent-mint/12 border border-accent-mint/30 flex items-center justify-center">
              <svg
                viewBox="0 0 24 24"
                className="w-5 h-5 text-accent-mint"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 2L4 6v6c0 5.5 3.4 10.6 8 12 4.6-1.4 8-6.5 8-12V6l-8-4z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <div>
              <div className="text-[18px] font-semibold tracking-tight text-txt-primary leading-none">
                TaxPilot <span className="text-accent-mint">AI</span>
              </div>
              <div className="text-[12px] text-txt-muted mt-1">
                GST Compliance &amp; Audit Intelligence
              </div>
            </div>
          </Link>
        </div>

        {/* Center Headline, 3 Feature Lines, and Reference-Inspired Card Stack */}
        <div className="my-10 lg:my-0 space-y-8 max-w-xl">
          <div className="space-y-4">
            <h1 className="text-[32px] sm:text-[38px] xl:text-[42px] leading-[1.12] font-semibold text-txt-primary tracking-tight">
              GST notice responses, investigated and drafted with evidence.
            </h1>

            <ul className="space-y-2.5 pt-1">
              {[
                'Reconcile GSTR-3B vs GSTR-2B',
                'Evidence-backed root causes',
                'Auditor-approved responses',
              ].map((line) => (
                <li
                  key={line}
                  className="flex items-center gap-2.5 text-[15px] leading-[24px] text-txt-secondary"
                >
                  <CheckCircle2 className="w-4 h-4 text-accent-mint shrink-0" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Floating Glass Reconciliation Stack (styled after "My cards") */}
          <div className="relative hidden sm:block pt-4">
            {/* Warm orange glow behind stack */}
            <div
              aria-hidden="true"
              className="absolute -top-6 right-8 w-64 h-64 rounded-full bg-brand-orange/20 blur-[70px] pointer-events-none"
            />

            {/* Stacked background layer 2 */}
            <div className="mx-6 h-10 rounded-t-card bg-white/[0.04] border border-b-0 border-border-subtle px-5 flex items-center justify-between text-[12px] text-txt-muted backdrop-blur-md">
              <span className="font-mono tabular-nums">INV-2024-0811 • Supplier Return</span>
              <span className="tabular-nums text-accent-mint font-medium">₹ 48,200.00</span>
            </div>

            {/* Stacked background layer 1 */}
            <div className="mx-3 h-10 -mt-2 rounded-t-card bg-white/[0.06] border border-b-0 border-border-subtle px-5 flex items-center justify-between text-[12px] text-txt-secondary backdrop-blur-md">
              <span className="font-mono tabular-nums">DRC-01A • Sec 16(2)(c) Check</span>
              <span className="tabular-nums text-txt-primary font-medium">₹ 93,600.00</span>
            </div>

            {/* Foreground Primary Reconciliation Card */}
            <div className="relative -mt-2 rounded-card bg-elevated/90 border border-border-strong p-5 shadow-glass backdrop-blur-xl">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-inner bg-brand-orange/15 border border-brand-orange/30 flex items-center justify-center text-brand-orange">
                    <FileSpreadsheet className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-[15px] font-medium text-txt-primary">
                      ITC Reconciliation Summary
                    </div>
                    <div className="text-[12px] font-mono tabular-nums text-txt-muted">
                      GSTIN 27AABCT1234C1Z5
                    </div>
                  </div>
                </div>
                <StatusBadge status="SUPPORTED" label="Matched" />
              </div>

              {/* Mini Area Sparkline + Variance Metric */}
              <div className="grid grid-cols-12 gap-4 items-end mb-4">
                <div className="col-span-5">
                  <div className="text-[12px] text-txt-muted">Net Variance</div>
                  <div className="text-[26px] leading-[32px] font-medium tabular-nums text-txt-primary mt-0.5">
                    ₹ 81,000.00
                  </div>
                  <div className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 rounded-full bg-accent-green/12 text-accent-green text-[11.5px] font-medium tabular-nums">
                    <ArrowUpRight className="w-3 h-3" />
                    <span>94.2% Verified</span>
                  </div>
                </div>
                <div className="col-span-7 h-16">
                  <svg viewBox="0 0 240 64" className="w-full h-full overflow-visible" aria-hidden="true">
                    <defs>
                      <linearGradient id="loginAreaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#FF6803" stopOpacity="0.5" />
                        <stop offset="100%" stopColor="#FF6803" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    <path
                      d="M0,48 C25,44 40,26 65,30 C90,34 110,16 135,22 C160,28 185,12 210,18 L240,14 L240,64 L0,64 Z"
                      fill="url(#loginAreaGrad)"
                    />
                    <path
                      d="M0,48 C25,44 40,26 65,30 C90,34 110,16 135,22 C160,28 185,12 210,18 L240,14"
                      fill="none"
                      stroke="#FF6803"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <circle cx="210" cy="18" r="4" fill="#FFFFFF" />
                  </svg>
                </div>
              </div>

              {/* Two Invoice Chip Rows */}
              <div className="space-y-2">
                <div className="flex items-center justify-between px-3.5 py-2.5 rounded-inner bg-surface-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="w-2 h-2 rounded-full bg-accent-mint shrink-0" />
                    <span className="text-[13px] text-txt-primary truncate font-mono tabular-nums">
                      INV-4092 • Apex Metals Pvt Ltd
                    </span>
                  </div>
                  <span className="text-[13px] font-medium tabular-nums text-accent-mint shrink-0">
                    +₹ 54,000.00
                  </span>
                </div>
                <div className="flex items-center justify-between px-3.5 py-2.5 rounded-inner bg-surface-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="w-2 h-2 rounded-full bg-brand-orange shrink-0" />
                    <span className="text-[13px] text-txt-primary truncate font-mono tabular-nums">
                      INV-4108 • Timing Difference
                    </span>
                  </div>
                  <span className="text-[13px] font-medium tabular-nums text-brand-amber shrink-0">
                    ₹ 27,000.00
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Caption */}
        <div className="text-[12.5px] text-txt-muted flex flex-wrap items-center gap-x-5 gap-y-2">
          <span>Deterministic Verification Gate</span>
          <span>•</span>
          <span>Mandatory Auditor Sign-Off</span>
        </div>
      </div>

      {/* Right 45%: Glass Sign-In Card */}
      <div className="relative lg:w-[45%] flex items-center justify-center p-6 sm:p-10 lg:p-14">
        <div className="w-full max-w-[430px]">
          <GlassCard elevated padding="lg" className="border-border-strong">
            <div className="mb-6">
              <h2 className="text-[24px] leading-[30px] font-semibold text-txt-primary tracking-tight">
                Sign in to TaxPilot AI
              </h2>
              <p className="text-[14px] text-txt-secondary mt-1">
                Access your Auditor or Admin compliance workspace.
              </p>
            </div>

            {error && (
              <div
                role="alert"
                className="mb-5 p-3.5 rounded-inner bg-danger/12 border border-danger/30 text-[13px] text-danger flex items-start gap-2.5"
              >
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} noValidate className="space-y-4">
              <Input
                id="login-email"
                label="Work Email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (emailError) setEmailError('')
                }}
                placeholder="ca@abctraders.demo"
                leftIcon={<Mail className="w-4 h-4" />}
                error={emailError}
              />

              <Input
                id="login-password"
                label="Password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (passwordError) setPasswordError('')
                }}
                placeholder="Enter your password"
                leftIcon={<Lock className="w-4 h-4" />}
                error={passwordError}
              />

              <div className="flex items-center justify-between pt-1">
                <label className="inline-flex items-center gap-2 text-[13px] text-txt-secondary cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-border-strong bg-surface-2 accent-[#FF6803]"
                  />
                  <span>Remember work email</span>
                </label>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                rightIcon={<ArrowRight className="w-4 h-4" />}
                className="w-full mt-2"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {/* Quick Demo Credentials */}
            <div className="mt-6 pt-5 border-t border-border-subtle">
              <div className="text-[12px] font-medium uppercase tracking-[0.06em] text-txt-muted mb-3">
                Demo Workspaces
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <button
                  type="button"
                  onClick={fillAuditorDemo}
                  className="px-3.5 py-2.5 rounded-inner bg-surface-2 hover:bg-surface-3 border border-border-subtle hover:border-border-strong text-left transition-colors"
                >
                  <div className="text-[13px] font-medium text-accent-mint">
                    Auditor
                  </div>
                  <div className="text-[12px] font-mono text-txt-muted truncate">
                    ca@abctraders.demo
                  </div>
                </button>
                <button
                  type="button"
                  onClick={fillAdminDemo}
                  className="px-3.5 py-2.5 rounded-inner bg-surface-2 hover:bg-surface-3 border border-border-subtle hover:border-border-strong text-left transition-colors"
                >
                  <div className="text-[13px] font-medium text-brand-amber">
                    Admin
                  </div>
                  <div className="text-[12px] font-mono text-txt-muted truncate">
                    {DEMO_CREDENTIALS.email}
                  </div>
                </button>
              </div>
            </div>

            <div className="mt-6 text-center text-[13px] text-txt-secondary">
              Need an organization workspace?{' '}
              <Link
                to="/auth/register"
                className="text-brand-orange font-medium hover:text-brand-amber hover:underline"
              >
                Register firm
              </Link>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
