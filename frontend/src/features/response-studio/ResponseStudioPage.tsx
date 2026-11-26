import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { ArrowLeft, FileCheck2, Download, Printer } from 'lucide-react'

export function ResponseStudioPage() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<any>(null)

  useEffect(() => {
    async function loadReport() {
      try {
        const res = await api.get(`/reports/${id}`)
        if (res.data.success) setReport(res.data.data)
      } catch (e) {}
    }
    if (id) loadReport()
  }, [id])

  const handleDownload = () => {
    const token = localStorage.getItem('taxpilot_token') || ''
    window.open(`/api/v1/reports/${id}/download?token=${encodeURIComponent(token)}`, '_blank')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to={`/app/investigations/${id}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563A6] hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Workspace
        </Link>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm flex items-center gap-1.5"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download PDF Package</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
        <h1 className="text-xl font-bold text-[#172B4D] flex items-center gap-2">
          <FileCheck2 className="w-5 h-5 text-[#2E8B83]" /> Response Drafting Studio
        </h1>

        <div className="p-6 bg-[#F5F7FA] rounded-xl border border-[#E2E8F0] space-y-4 text-xs leading-relaxed">
          <div className="font-bold text-[#173B67] text-base">
            REPLY TO GST NOTICE INTIMATION (FORM GST DRC-01A)
          </div>
          <div className="text-slate-800">
            <b>Statutory Grounds:</b> Section 16(2) of CGST Act, 2017 & CBIC Circular No. 183/15/2022-GST.
          </div>
          <p className="text-slate-700">
            {report?.content?.executive_summary || 'The taxpayer respectfully submits that the discrepancy of INR 81,000 arises due to a timing difference in supplier reporting under GSTR-1, which has since been rectified in subsequent portal statements.'}
          </p>
          <div className="text-slate-700 whitespace-pre-line">
            {report?.content?.legal_submissions}
          </div>
          <p className="text-slate-700 font-semibold">
            {report?.content?.prayer || 'In view of the verified evidence, it is respectfully prayed that the proposed demand be dropped.'}
          </p>
        </div>
      </div>
    </div>
  )
}
