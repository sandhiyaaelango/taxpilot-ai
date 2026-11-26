import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import { Building2, ShieldCheck, Mail, Phone, MapPin, ArrowLeft, Plus, FileSearch, ArrowRight } from 'lucide-react'

export function ClientProfilePage() {
  const { id } = useParams<{ id: string }>()
  const [client, setClient] = useState<any>(null)
  const [investigations, setInvestigations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadClientData() {
      try {
        const [clientRes, invsRes] = await Promise.all([
          api.get(`/clients/${id}`),
          api.get(`/investigations?client_id=${id}`)
        ])
        if (clientRes.data.success) setClient(clientRes.data.data)
        if (invsRes.data.success) setInvestigations(invsRes.data.data)
      } catch (err) {
        console.error('Failed to load client details', err)
      } finally {
        setLoading(false)
      }
    }
    if (id) loadClientData()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (!client) {
    return <div className="text-sm text-red-600">Client not found.</div>
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link to="/app/clients" className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563A6] hover:underline">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Clients List
      </Link>

      {/* Profile Header Card */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-[#172B4D]">{client.business_name}</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-800">
                {client.status}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-2">
              <span className="font-mono font-bold text-[#2563A6] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                {client.primary_gstin}
              </span>
              <span>State Code: {client.state_code}</span>
              <span>Industry: {client.industry}</span>
            </div>
          </div>

          <Link
            to="/app/investigations"
            className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5 self-start md:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Launch Notice Investigation</span>
          </Link>
        </div>

        {/* GSTIN Profiles Registered */}
        <div className="mt-6 pt-5 border-t border-[#E2E8F0]">
          <h3 className="text-xs font-bold text-[#172B4D] uppercase tracking-wider mb-3">
            Registered GSTIN Branches & Profiles
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {(client.gstin_profiles || []).map((g: any) => (
              <div key={g.id} className="p-3 bg-[#F5F7FA] rounded-lg border border-[#E2E8F0] text-xs">
                <div className="font-mono font-bold text-[#172B4D]">{g.gstin}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{g.trade_name || client.business_name}</div>
                {g.is_primary && (
                  <span className="inline-block mt-2 text-[10px] font-bold text-[#2E8B83] bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
                    Primary Entity
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Client's Investigations */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
          <h2 className="font-bold text-sm text-[#172B4D]">GST Notice Inquiries for this Client</h2>
        </div>
        {investigations.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No active notice investigations for this client yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#E2E8F0]">
                <tr>
                  <th className="px-5 py-3">Investigation</th>
                  <th className="px-5 py-3">Tax Period</th>
                  <th className="px-5 py-3">ITC Mismatch</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {investigations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-semibold text-[#172B4D]">{inv.title}</td>
                    <td className="px-5 py-3.5 text-slate-500">{inv.tax_period}</td>
                    <td className="px-5 py-3.5 font-bold text-[#172B4D]">{formatCurrency(inv.mismatch_amount)}</td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getStatusBadgeClass(inv.status)}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link to={`/app/investigations/${inv.id}`} className="text-xs font-semibold text-[#2563A6] hover:underline">
                        Open Workspace
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
