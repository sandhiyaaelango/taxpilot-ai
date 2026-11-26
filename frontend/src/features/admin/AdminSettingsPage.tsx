import React, { useState } from 'react'
import { Settings, Save, CheckCircle2 } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'

export function AdminSettingsPage() {
  const [sessionTimeout, setSessionTimeout] = useState('60')
  const [maxUploadSize, setMaxUploadSize] = useState('15')
  const [requireOcr, setRequireOcr] = useState(true)
  const [saved, setSaved] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        badge={{ icon: <Settings className="w-3.5 h-3.5" />, label: 'Enterprise Governance' }}
        title="Application Security & Settings"
        description="Configure organization compliance thresholds, session policies, and document upload quotas."
      />

      {saved && (
        <div className="p-3.5 rounded-inner bg-status-success/15 border border-status-success/30 text-xs text-status-success flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Application settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave}>
        <GlassCard className="p-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                User Session Timeout (Minutes)
              </label>
              <Input
                type="number"
                value={sessionTimeout}
                onChange={(e) => setSessionTimeout(e.target.value)}
                className="font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Max Notice File Size (MB)
              </label>
              <Input
                type="number"
                value={maxUploadSize}
                onChange={(e) => setMaxUploadSize(e.target.value)}
                className="font-mono"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="flex items-start gap-3 cursor-pointer p-4 bg-surface-2 rounded-inner border border-white/8 hover:border-brand-orange/30 transition-colors">
                <div className="relative mt-0.5">
                  <input
                    type="checkbox"
                    checked={requireOcr}
                    onChange={(e) => setRequireOcr(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-8 h-5 rounded-full bg-surface-3 peer-checked:bg-brand-orange transition-colors" />
                  <div className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform peer-checked:translate-x-3" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-white">
                    Enforce OCR Scanned Notice Fallback Analysis
                  </div>
                  <div className="text-[11px] text-text-muted mt-0.5">
                    PyMuPDF / Tesseract fallback when native PDF text extraction fails
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-white/5">
            <Button type="submit" variant="primary" size="sm" icon={<Save className="w-4 h-4" />}>
              Save Settings
            </Button>
          </div>
        </GlassCard>
      </form>
    </div>
  )
}
