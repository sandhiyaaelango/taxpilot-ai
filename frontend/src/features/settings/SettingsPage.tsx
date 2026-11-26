import React from 'react'
import { useAuthStore } from '@/stores/authStore'
import { Settings, Shield, Server, Key, Building2 } from 'lucide-react'

export function SettingsPage() {
  const { user } = useAuthStore()

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#172B4D] tracking-tight">System & Workspace Settings</h1>
        <p className="text-xs text-[#64748B] mt-1">
          Manage CA firm profile, FastMCP servers, and Gemini API keys
        </p>
      </div>

      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-6">
        {/* Profile */}
        <div>
          <h3 className="font-bold text-sm text-[#172B4D] mb-4 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#173B67]" /> Organization Profile
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-500 mb-1">Chartered Accountant</label>
              <input
                type="text"
                disabled
                value={user?.full_name || 'Rajesh Sharma'}
                className="w-full p-2.5 bg-[#F5F7FA] border border-[#E2E8F0] rounded-lg text-[#172B4D] font-medium"
              />
            </div>
            <div>
              <label className="block text-slate-500 mb-1">Email Address</label>
              <input
                type="text"
                disabled
                value={user?.email || 'admin@abctraders.demo'}
                className="w-full p-2.5 bg-[#F5F7FA] border border-[#E2E8F0] rounded-lg text-[#172B4D] font-medium"
              />
            </div>
          </div>
        </div>

        {/* MCP Configuration */}
        <div className="pt-6 border-t border-[#E2E8F0]">
          <h3 className="font-bold text-sm text-[#172B4D] mb-4 flex items-center gap-2">
            <Server className="w-4 h-4 text-[#2563A6]" /> FastMCP Server Endpoints
          </h3>
          <div className="space-y-3 text-xs">
            <div className="p-3 bg-[#F5F7FA] rounded-lg flex items-center justify-between">
              <div>
                <span className="font-bold text-[#172B4D]">Tax Portal MCP Server</span>
                <span className="block text-[11px] text-slate-500 font-mono mt-0.5">http://localhost:8001/mcp</span>
              </div>
              <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded font-bold text-[10px]">CONNECTED</span>
            </div>

            <div className="p-3 bg-[#F5F7FA] rounded-lg flex items-center justify-between">
              <div>
                <span className="font-bold text-[#172B4D]">Ledger MCP Server</span>
                <span className="block text-[11px] text-slate-500 font-mono mt-0.5">http://localhost:8002/mcp</span>
              </div>
              <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded font-bold text-[10px]">CONNECTED</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
