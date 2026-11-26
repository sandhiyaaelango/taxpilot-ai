import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatDate } from '@/utils'
import { Users, Plus, Search, Building2, MapPin, ArrowRight, ShieldCheck, X } from 'lucide-react'

export function ClientsPage() {
  const [clients, setClients] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    business_name: '',
    primary_gstin: '',
    contact_name: '',
    contact_email: '',
    industry: 'Wholesale & Distribution'
  })
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchClients = async () => {
    try {
      const res = await api.get(`/clients?search=${encodeURIComponent(search)}`)
      if (res.data.success) {
        setClients(res.data.data)
      }
    } catch (err) {
      console.error('Failed to load clients', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClients()
  }, [search])

  const handleCreateClient = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setFormError('')
    try {
      const res = await api.post('/clients', formData)
      if (res.data.success) {
        setModalOpen(false)
        setFormData({ business_name: '', primary_gstin: '', contact_name: '', contact_email: '', industry: 'Wholesale & Distribution' })
        fetchClients()
      }
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to create client')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#172B4D] tracking-tight">Client Workspace</h1>
          <p className="text-xs text-[#64748B] mt-1">
            Manage corporate client accounts, multiple GSTIN profiles, and notice history
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm transition-all flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Client</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex items-center gap-3">
        <Search className="w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by client business name, GSTIN, or contact person..."
          className="w-full text-xs border-0 focus:outline-none focus:ring-0 text-[#172B4D]"
        />
      </div>

      {/* Clients Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {clients.map((client) => (
            <div key={client.id} className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-5 hover:shadow-md transition-shadow flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-bold text-sm text-[#172B4D] leading-snug">{client.business_name}</h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-800 shrink-0">
                    {client.status}
                  </span>
                </div>

                <div className="space-y-1.5 text-xs text-slate-600 mb-4">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] text-[#2563A6] font-semibold">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{client.primary_gstin}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    <span>{client.industry || 'General Business'}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    <span>State Code: {client.state_code}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-[#E2E8F0] flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  {client.contact_name ? `Contact: ${client.contact_name}` : 'Multi-GSTIN'}
                </span>
                <Link
                  to={`/app/clients/${client.id}`}
                  className="text-xs font-semibold text-[#2563A6] hover:text-[#173B67] flex items-center gap-1"
                >
                  View Profile <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Client Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl border border-[#E2E8F0] w-full max-w-md overflow-hidden">
            <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between">
              <h3 className="font-bold text-sm text-[#172B4D]">Add Client Profile</h3>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="mx-5 mt-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateClient} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#172B4D] mb-1">Company / Business Name *</label>
                <input
                  type="text"
                  required
                  value={formData.business_name}
                  onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                  placeholder="Apex Global Pvt Ltd"
                  className="w-full text-xs px-3 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172B4D] mb-1">Primary GSTIN (15 chars) *</label>
                <input
                  type="text"
                  required
                  maxLength={15}
                  value={formData.primary_gstin}
                  onChange={(e) => setFormData({ ...formData, primary_gstin: e.target.value.toUpperCase() })}
                  placeholder="27AABCT1234C1Z5"
                  className="w-full text-xs px-3 py-2 font-mono uppercase border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#172B4D] mb-1">Contact Name</label>
                  <input
                    type="text"
                    value={formData.contact_name}
                    onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                    placeholder="Deepak Sharma"
                    className="w-full text-xs px-3 py-2 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#172B4D] mb-1">Contact Email</label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    placeholder="finance@apex.in"
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
                  {submitting ? 'Creating...' : 'Create Client'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
