import React, { useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '@/services/api/client'
import { Upload, FileText, ArrowLeft, CheckCircle2, AlertTriangle, FileUp, Sparkles } from 'lucide-react'

export function NoticeUploadPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [activeTab, setActiveTab] = useState<'FILE' | 'TEXT'>('FILE')
  const [file, setFile] = useState<File | null>(null)
  const [noticeText, setNoticeText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a PDF or image notice file to upload')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (id) {
        formData.append('investigation_id', id)
      }

      const res = await api.post('/notices/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (res.data.success) {
        setUploadResult(res.data.data)
        setSuccess(true)
        const targetInvId = res.data.data.investigation_id || id
        setTimeout(() => navigate(`/app/investigations/${targetInvId}`), 1800)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload notice file')
    } finally {
      setSubmitting(false)
    }
  }

  const handleTextUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('notice_text', noticeText)
      const res = await api.post(`/investigations/${id}/notice`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (res.data.success) {
        setSuccess(true)
        setTimeout(() => navigate(`/app/investigations/${id}`), 1200)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error uploading notice text')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Link to={`/app/investigations/${id || ''}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#2563A6] hover:underline">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Investigation Workspace
      </Link>

      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-[#172B4D]">Upload GST Notice Document</h1>
          <p className="text-xs text-[#64748B] mt-1">
            Upload an official GST notice PDF (DRC-01, DRC-01A, DRC-01C, ASMT-10) to initiate automated multi-agent extraction and ITC mismatch verification.
          </p>
        </div>

        {/* Tab selection */}
        <div className="flex border-b border-[#E2E8F0] gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('FILE')}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'FILE'
                ? 'border-[#173B67] text-[#173B67]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileUp className="w-4 h-4" /> PDF Document Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('TEXT')}
            className={`pb-2.5 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
              activeTab === 'TEXT'
                ? 'border-[#173B67] text-[#173B67]'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileText className="w-4 h-4" /> Paste Notice Text
          </button>
        </div>

        {success && (
          <div className="p-4 bg-emerald-50 text-emerald-800 text-xs rounded-lg border border-emerald-200 space-y-2">
            <div className="flex items-center gap-2 font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Notice uploaded and parsed successfully! Redirecting...
            </div>
            {uploadResult?.notice && (
              <div className="text-[11px] text-emerald-700 bg-white/60 p-2.5 rounded border border-emerald-200 font-mono space-y-1">
                <div>Notice Type: {uploadResult.notice.notice_type || 'DRC-01'}</div>
                <div>GSTIN: {uploadResult.notice.gstin || 'Extracted'}</div>
                <div>ITC Mismatch: INR {uploadResult.notice.itc_mismatch?.toLocaleString()}</div>
                <div>Status: {uploadResult.notice.status}</div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" /> {error}
          </div>
        )}

        {activeTab === 'FILE' ? (
          <form onSubmit={handleFileUpload} className="space-y-4">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#ADC7E7] hover:border-[#2563A6] bg-[#F5F7FA] hover:bg-[#EEF3FA] rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors text-center"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="hidden"
              />
              <Upload className="w-10 h-10 text-[#2563A6] mb-3" />
              {file ? (
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-[#172B4D]">{file.name}</div>
                  <div className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB — Click to change file</div>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-[#172B4D]">Choose GST Notice PDF or Drag & Drop</div>
                  <div className="text-xs text-slate-500">Supports PDF, PNG, JPG up to 20MB</div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-[#2E8B83]" /> Automated PyMuPDF & Structured Extraction
              </span>
              <button
                type="submit"
                disabled={submitting || !file || success}
                className="px-6 py-2.5 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 flex items-center gap-2"
              >
                {submitting ? 'Extracting & Parsing Notice...' : 'Upload & Start Investigation'}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleTextUpload} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#172B4D] mb-1">
                Notice Text Content (DRC-01 / DRC-01A / ASMT-10)
              </label>
              <textarea
                rows={8}
                required
                value={noticeText}
                onChange={(e) => setNoticeText(e.target.value)}
                placeholder="FORM GST DRC-01A&#10;Notice Number: ZA271223001928K&#10;Taxpayer GSTIN: 27AABCT1234C1Z5&#10;Tax Period: 2023-11&#10;Excess ITC claimed: INR 81,000.00&#10;..."
                className="w-full text-xs font-mono p-3 border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563A6]"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="submit"
                disabled={submitting || success}
                className="px-5 py-2.5 bg-[#173B67] hover:bg-[#1E4F87] text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                {submitting ? 'Uploading...' : 'Save & Trigger Parser'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
