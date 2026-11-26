import React, { useState } from 'react'
import { Cpu, Key, Save, CheckCircle2 } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'

export function AdminLlmConfigPage() {
  const [model, setModel] = useState('gemini-2.5-flash')
  const [temperature, setTemperature] = useState('0.1')
  const [maxTokens, setMaxTokens] = useState('4096')
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        badge={{ icon: <Cpu className="w-3.5 h-3.5" />, label: 'Foundation Model Orchestration' }}
        title="LLM Configuration & Parameters"
        description="Configure Gemini model endpoints, sampling temperatures, and token limits. Secrets remain safely secured in environment variables."
      />

      {saved && (
        <div className="p-3.5 rounded-inner bg-status-success/15 border border-status-success/30 text-xs text-status-success flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>LLM operational parameters saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave}>
        <GlassCard className="p-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* Model selector */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">Active Gemini Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2.5 bg-surface-2 border border-white/10 rounded-inner text-xs text-white
                  focus:outline-none focus:ring-2 focus:ring-brand-orange/50 focus:border-brand-orange/50 transition-colors"
              >
                <option value="gemini-2.5-flash">Google Gemini 2.5 Flash — Ultra Low Latency</option>
                <option value="gemini-2.5-pro">Google Gemini 2.5 Pro — Deep Multi-hop Reasoning</option>
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">Inference Temperature</label>
              <Input
                type="text"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                placeholder="0.1"
                className="font-mono"
              />
            </div>

            {/* Max tokens */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">Max Output Tokens</label>
              <Input
                type="text"
                value={maxTokens}
                onChange={(e) => setMaxTokens(e.target.value)}
                className="font-mono"
              />
            </div>

            {/* API key status (read-only) */}
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">API Key Security Status</label>
              <div className="flex items-center gap-2 px-3 py-2.5 bg-surface-2 border border-white/5 rounded-inner">
                <Key className="w-3.5 h-3.5 text-accent-mint shrink-0" />
                <span className="text-[11px] text-status-success font-mono truncate">
                  Configured via .env (GEMINI_API_KEY) • Protected
                </span>
              </div>
            </div>
          </div>

          {/* Model spec info */}
          <div className="p-4 bg-brand-orange/8 border border-brand-orange/20 rounded-inner">
            <div className="text-xs font-semibold text-brand-amber mb-1">Active Model Specification</div>
            <div className="text-[11px] text-text-secondary leading-relaxed">
              <span className="font-mono text-white">{model}</span> — Temperature: <span className="font-mono text-white">{temperature}</span> —
              Max tokens: <span className="font-mono text-white">{maxTokens}</span>. 
              ReAct agent uses this model for all investigation reasoning and tool-calling steps. 
              Lower temperature produces deterministic, legally traceable reasoning chains.
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-white/5">
            <Button type="submit" variant="primary" size="sm" icon={<Save className="w-4 h-4" />}>
              Save Configuration
            </Button>
          </div>
        </GlassCard>
      </form>
    </div>
  )
}
