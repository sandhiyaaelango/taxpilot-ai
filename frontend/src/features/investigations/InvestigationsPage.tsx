import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import { FileSearch, Plus, Filter, ArrowRight, ShieldAlert, Sparkles, X } from 'lucide-react'

export function InvestigationsPage() {
  const [investigations, setInvestigations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [clients, setClients] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    client_id: '',
    title: '',
    tax_period: '2023-11',
    mismatch_amount: 81000.0,
    description: 'DRC-01A ITC Mismatch Investigation'
  })
  const [submitting, setSubmitting] = useState(false)

  const fetchInvestigations = async () => {
    try {
      const url = statusFilter ? `/investigations?status=${statusFilter}` : '/investigations'
      const res = await api.get(url)
      if (res.data.success) {
        setInvestigations(res.data.data)
      }
    } catch (err) {
      console.error('Failed to load investigations', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInvestigations()
  }, [statusFilter])

  useEffect(() => {
    async function loadClients() {
      try {
        const res = await api.get('/clients')
        if (res.data.success && res.data.data.length > 0) {
          setClients(res.data.data)
          setFormData(prev => ({ ...prev, client_id: res.data.data[0].id }))
        }
      } catch (e) {}
    }
    loadClients()
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await api.post('/investigations', formData)
      if (res.data.success) {
        setModalOpen(false)
        fetchInvestigations()
      }
    } catch (err) {
      alert('Failed to create investigation')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172B4D] tracking-tight">GST Notice Investigations</h1>
          <p className="text-xs text-[#64748B] mt-1">
            Active multi-agent inquiries, evidence challenge loops, and response drafts
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>New Investigation</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#E2E8F0] pb-3 text-xs">
        <button
          onClick={() => setStatusFilter('')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            statusFilter === '' ? 'bg-[#173B67] text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setStatusFilter('AWAITING_APPROVAL')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            statusFilter === 'AWAITING_APPROVAL' ? 'bg-[#2E8B83] text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Awaiting Approval
        </button>
        <button
          onClick={() => setStatusFilter('INVESTIGATING')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            statusFilter === 'INVESTIGATING' ? 'bg-[#2563A6] text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Investigating
        </button>
        <button
          onClick={() => setStatusFilter('APPROVED')}
          className={`px-3 py-1.5 rounded-lg font-semibold transition-colors ${
            statusFilter === 'APPROVED' ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Approved
        </button>
      </div>

      {/* Investigations Table */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#E2E8F0]">
                <tr>
                  <th className="px-5 py-3">Inquiry Title</th>
                  <th className="px-5 py-3">Client Entity</th>
                  <th className="px-5 py-3">Tax Period</th>
                  <th className="px-5 py-3">ITC Mismatch</th>
                  <th className="px-5 py-3">Deadline</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {investigations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-4">
                      <div className="font-semibold text-[#172B4D] text-sm">{inv.title}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{inv.description}</div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-[#172B4D]">{inv.client_business_name}</div>
                      <div className="text-[11px] font-mono text-slate-400">{inv.client_gstin}</div>
                    </td>
                    <td className="px-5 py-4 font-mono text-slate-600">
                      {inv.tax_period}
                    </td>
                    <td className="px-5 py-4 font-bold text-[#172B4D]">
                      {formatCurrency(inv.mismatch_amount)}
                    </td>
                    <td className="px-5 py-4 text-slate-500">
                      {formatDate(inv.response_deadline)}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${getStatusBadgeClass(inv.status)}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        to={`/app/investigations/${inv.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#173B67] hover:bg-[#1E4F87] text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                      >
                        <span>Workspace</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* New Investigation Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-[#E2E8F0] w-full max-w-md overflow-hidden">
            <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
              <h3 className="font-bold text-sm text-[#172B4D]">Create Investigation Record</h3>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#172B4D] mb-1">Target Client *</label>
                <select
                  required
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                  className="w-full text-xs px-3 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6] bg-white"
                >
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.business_name} ({c.primary_gstin})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172B4D] mb-1">Investigation Title *</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="GST DRC-01A Timing & Non-Filing Inquiry"
                  className="w-full text-xs px-3 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#172B4D] mb-1">Tax Period (YYYY-MM)</label>
                  <input
                    type="text"
                    required
                    value={formData.tax_period}
                    onChange={(e) => setFormData({ ...formData, tax_period: e.target.value })}
                    className="w-full text-xs px-3 py-2 font-mono border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#172B4D] mb-1">Mismatch Amount (INR)</label>
                  <input
                    type="number"
                    required
                    value={formData.mismatch_amount}
                    onChange={(e) => setFormData({ ...formData, mismatch_amount: parseFloat(e.target.value) })}
                    className="w-full text-xs px-3 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-[#E2E8F0]">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-3.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Initialize Investigation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
