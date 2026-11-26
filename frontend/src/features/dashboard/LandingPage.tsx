import React from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldCheck,
  FileSpreadsheet,
  FileCheck2,
  Lock,
  ArrowRight,
  Server,
  Scale,
  FileSearch,
  TrendingUp,
  Cpu
} from 'lucide-react'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-base text-white relative overflow-hidden">
      {/* Ambient glows */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/3 w-[600px] h-[600px] rounded-full bg-brand-orange/7 blur-[150px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-brand-amber/5 blur-[150px]" />
        <div className="absolute top-2/3 left-0 w-[400px] h-[400px] rounded-full bg-brand-orange/4 blur-[120px]" />
      </div>

      {/* Top Navbar */}
      <header className="relative z-20 bg-bg-elevated/80 backdrop-blur-xl border-b border-white/6 h-16 px-6 md:px-12 flex items-center justify-between sticky top-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-orange/80 to-brand-amber/60 border border-brand-orange/40 flex items-center justify-center shadow-orange-glow">
            <FileSearch className="w-4.5 h-4.5 text-white" />
          </div>
          <span className="font-outfit font-semibold text-lg tracking-tight text-white">
            TaxPilot <span className="text-brand-orange">AI</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/auth/login"
            className="px-4 py-1.5 rounded-nav text-xs font-semibold text-text-secondary
              bg-surface-1 border border-white/8 hover:border-brand-orange/40 hover:text-white transition-all"
          >
            Sign In
          </Link>
          <Link
            to="/app/dashboard"
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-nav text-xs font-semibold text-white
              bg-brand-orange hover:bg-brand-amber shadow-orange-glow transition-all"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative z-10 pt-24 pb-16 px-6 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-orange/12 border border-brand-orange/25 text-[11px] font-semibold text-brand-amber mb-7">
          <ShieldCheck className="w-3.5 h-3.5 text-brand-orange" />
          Institutional GST Notice Investigation &amp; Compliance Platform
        </div>

        <h1 className="font-outfit text-4xl sm:text-5xl md:text-[56px] font-semibold tracking-tight text-white leading-[1.1] mb-6">
          Statutory GST Reconciliation &amp;{' '}
          <span className="text-brand-orange">Audit-Ready</span> Defense
        </h1>

        <p className="text-sm sm:text-base text-text-secondary max-w-2xl mx-auto mb-10 leading-relaxed">
          Built for Chartered Accountants and enterprise tax teams to dissect GST ITC mismatch notices,
          reconcile GSTR-2B &amp; purchase ledgers, verify Section 16(2) compliance, and issue
          verified replies with mandatory human approval.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/auth/login"
            className="inline-flex items-center gap-2 px-7 py-3 rounded-pill text-sm font-semibold text-white
              bg-brand-orange hover:bg-brand-amber shadow-orange-glow transition-all"
          >
            <span>Enter CA Audit Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/auth/register"
            className="inline-flex items-center gap-2 px-7 py-3 rounded-pill text-sm font-semibold text-text-secondary
              bg-surface-1 border border-white/8 hover:border-brand-orange/40 hover:text-white transition-all"
          >
            Register Firm
          </Link>
        </div>

        {/* Stats strip */}
        <div className="mt-14 grid grid-cols-3 gap-6 max-w-lg mx-auto">
          {[
            { label: 'Investigation Accuracy', value: '99.2%' },
            { label: 'Avg. Processing Time', value: '< 90s' },
            { label: 'MCP Tool Calls / Run', value: '12–18' }
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-semibold font-outfit text-brand-orange tabular-nums">{stat.value}</div>
              <div className="text-[10px] text-text-muted mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* 3 Pillars */}
      <section className="relative z-10 py-10 px-6 max-w-5xl mx-auto">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              icon: FileSpreadsheet,
              color: 'text-brand-orange',
              bg: 'bg-brand-orange/10 border-brand-orange/20',
              title: 'Mismatch-Level Fan-Out',
              desc: 'Decomposes DRC-01A & ASMT-10 notices into individual invoice mismatches, running isolated ledger and portal checks per variance.'
            },
            {
              icon: Scale,
              color: 'text-brand-amber',
              bg: 'bg-brand-amber/10 border-brand-amber/20',
              title: 'Deterministic Verification Gate',
              desc: 'Enforces Python-verified ITC arithmetic and source provenance before drafting, isolating supported, contradicted, and unverified items.'
            },
            {
              icon: FileCheck2,
              color: 'text-accent-mint',
              bg: 'bg-accent-mint/10 border-accent-mint/20',
              title: 'Auditor Final Sign-Off',
              desc: 'Halts automatically for Chartered Accountant review, legal draft refinement, final approval, and deterministic PDF annexure export.'
            }
          ].map((pillar) => {
            const Icon = pillar.icon
            return (
              <div
                key={pillar.title}
                className="p-6 rounded-card bg-surface-1 border border-white/6 backdrop-blur-sm hover:border-white/12 transition-all group"
              >
                <div className={`w-10 h-10 rounded-inner ${pillar.bg} border flex items-center justify-center mb-4`}>
                  <Icon className={`w-5 h-5 ${pillar.color}`} />
                </div>
                <h3 className="font-semibold text-sm text-white mb-2">{pillar.title}</h3>
                <p className="text-[11px] text-text-muted leading-relaxed">{pillar.desc}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Tech strip */}
      <section className="relative z-10 py-10 px-6 max-w-5xl mx-auto">
        <div className="p-6 rounded-card bg-surface-1 border border-white/6 backdrop-blur-sm">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { icon: Server, label: 'FastMCP Tax Portal & Ledger', color: 'text-accent-mint' },
              { icon: Cpu, label: 'Google Gemini 2.5 Flash', color: 'text-brand-orange' },
              { icon: TrendingUp, label: 'LangGraph ReAct Agents', color: 'text-brand-amber' },
              { icon: Lock, label: 'Strict Auditor & Admin Roles', color: 'text-accent-mint' }
            ].map((item) => {
              const Icon = item.icon
              return (
                <div key={item.label} className="flex flex-col items-center gap-2">
                  <Icon className={`w-5 h-5 ${item.color}`} />
                  <span className="text-[10px] text-text-muted">{item.label}</span>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 px-6 max-w-5xl mx-auto border-t border-white/5 mt-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <div className="w-6 h-6 rounded-lg bg-brand-orange/15 border border-brand-orange/25 flex items-center justify-center">
            <FileSearch className="w-3 h-3 text-brand-orange" />
          </div>
          <span>TaxPilot AI — GST Compliance Platform</span>
        </div>
        <div className="flex items-center gap-4 text-[11px] text-text-muted">
          <span className="flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-accent-mint" />
            FastMCP Integration
          </span>
          <span className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-brand-amber" />
            Role Separation Enforced
          </span>
        </div>
      </footer>
    </div>
  )
}
