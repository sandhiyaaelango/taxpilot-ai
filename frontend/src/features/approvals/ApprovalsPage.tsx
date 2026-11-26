import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency, formatDate, getStatusBadgeClass } from '@/utils'
import { FileCheck2, ArrowRight, CheckCircle2, Clock, ShieldCheck } from 'lucide-react'

export function ApprovalsPage() {
  const [pendingInvs, setPendingInvs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const fetchApprovals = async () => {
    try {
      const res = await api.get('/investigations?status=AWAITING_APPROVAL')
      if (res.data.success) {
        setPendingInvs(res.data.data)
      }
    } catch (err) {
      console.error('Failed to load pending approvals', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApprovals()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#172B4D] tracking-tight">Auditor Review & Approval Centre</h1>
        <p className="text-xs text-[#64748B] mt-1">
          Mandatory Auditor Human-in-the-Loop review gate. Responses cannot be finalized or exported without Auditor sign-off.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-3 border-[#173B67] border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : pendingInvs.length === 0 ? (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-12 text-center">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="font-bold text-sm text-[#172B4D]">All Responses Reviewed</h3>
          <p className="text-xs text-[#64748B] mt-1">
            There are currently no investigations awaiting Auditor sign-off.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F5F7FA] text-[#64748B] uppercase tracking-wider font-semibold border-b border-[#E2E8F0]">
                <tr>
                  <th className="px-5 py-3">Investigation</th>
                  <th className="px-5 py-3">Client Entity</th>
                  <th className="px-5 py-3">Period</th>
                  <th className="px-5 py-3">Mismatch Amount</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Review Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {pendingInvs.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-4 font-semibold text-[#172B4D]">{inv.title}</td>
                    <td className="px-5 py-4">
                      <div className="font-medium text-[#172B4D]">{inv.client_business_name}</div>
                      <div className="text-[11px] font-mono text-slate-400">{inv.client_gstin}</div>
                    </td>
                    <td className="px-5 py-4 font-mono text-slate-600">{inv.tax_period}</td>
                    <td className="px-5 py-4 font-bold text-[#172B4D]">{formatCurrency(inv.mismatch_amount)}</td>
                    <td className="px-5 py-4">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        to={`/app/investigations/${inv.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#173B67] hover:bg-[#1E4F87] text-white rounded-lg text-xs font-semibold shadow-2xs"
                      >
                        <span>Review & Sign-Off</span>
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
    </div>
  )
}
