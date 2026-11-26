import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import { Scale, ArrowLeft, ShieldCheck, FileText, CheckCircle2, XCircle } from 'lucide-react'

export function EvidencePage() {
  const { id } = useParams<{ id: string }>()
  const [evidenceData, setEvidenceData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchEvidence() {
      try {
        const res = await api.get(`/investigations/${id}/evidence`)
        if (res.data.success) {
          setEvidenceData(res.data.data)
        }
      } catch (err) {
        console.error('Failed to load evidence', err)
      } finally {
        setLoading(false)
      }
    }
    if (id) fetchEvidence()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link to={`/app/investigations/${id}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563A6] hover:underline">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Investigation Workspace
      </Link>

      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
        <h1 className="text-xl font-bold text-[#172B4D] flex items-center gap-2">
          <Scale className="w-5 h-5 text-[#2E8B83]" /> Evidence Intelligence & Provenance Records
        </h1>
        <p className="text-xs text-[#64748B]">
          Audit-grade evidence records collected through FastMCP tools from simulated tax portals and accounting ledgers.
        </p>

        {/* Evidence Records Table */}
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#E2E8F0]">
              <tr>
                <th className="px-4 py-3">Source ID</th>
                <th className="px-4 py-3">Document Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Tax Amount</th>
                <th className="px-4 py-3">Retrieved By</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E2E8F0]">
              {(evidenceData?.evidence_records || []).map((rec: any) => (
                <tr key={rec.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-mono font-bold text-[#2563A6]">{rec.source_id}</td>
                  <td className="px-4 py-3 font-medium text-[#172B4D]">{rec.document_name}</td>
                  <td className="px-4 py-3 text-slate-500">{rec.source_type}</td>
                  <td className="px-4 py-3 font-bold text-[#172B4D]">{formatCurrency(rec.amount)}</td>
                  <td className="px-4 py-3 text-slate-500">{rec.retrieved_by}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getStatusBadgeClass(rec.status)}`}>
                      {rec.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
