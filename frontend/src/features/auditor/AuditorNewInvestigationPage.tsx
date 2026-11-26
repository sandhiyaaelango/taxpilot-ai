import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/services/api/client'
import { formatCurrency } from '@/utils'
import {
  Upload,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Building2,
  X,
  RotateCcw,
  RefreshCw,
} from 'lucide-react'
import {
  GlassCard,
  Button,
  Input,
  SegmentedControl,
  StatusBadge,
  PageHeader,
  PdfUploadPreview,
  type UploadStage,
} from '@/components/ui'

const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/

function deriveFinancialYear(taxPeriod?: string | null): string {
  if (!taxPeriod) return ''
  // Matches YYYY-MM e.g. 2023-11 -> 2023-24, 2024-02 -> 2023-24
  const ym = taxPeriod.match(/^(\d{4})-(\d{2})$/)
  if (ym) {
    const year = parseInt(ym[1], 10)
    const month = parseInt(ym[2], 10)
    const startYear = month >= 4 ? year : year - 1
    return `${startYear}-${String((startYear + 1) % 100).padStart(2, '0')}`
  }
  return ''
}

interface FieldErrors {
  gstin?: string
  noticeNumber?: string
  noticeType?: string
  taxPeriod?: string
  mismatchAmount?: string
  responseDeadline?: string
}

export function AuditorNewInvestigationPage() {
  const navigate = useNavigate()
  const ledgerInputRef = useRef<HTMLInputElement>(null)

  const [activeTab, setActiveTab] = useState<'FILE' | 'TEXT'>('FILE')
  const [file, setFile] = useState<File | null>(null)
  const [ledgerFiles, setLedgerFiles] = useState<File[]>([])
  const [noticeText, setNoticeText] = useState('')
  const [clients, setClients] = useState<any[]>([])

  // Form Fields — intentionally empty until extracted or entered by auditor (never fabricated)
  const [clientId, setClientId] = useState('')
  const [taxpayerName, setTaxpayerName] = useState('')
  const [gstin, setGstin] = useState('')
  const [noticeNumber, setNoticeNumber] = useState('')
  const [financialYear, setFinancialYear] = useState('')
  const [taxPeriod, setTaxPeriod] = useState('')
  const [noticeType, setNoticeType] = useState('')
  const [noticeSection, setNoticeSection] = useState('')
  const [taxType, setTaxType] = useState('')
  const [mismatchAmount, setMismatchAmount] = useState('')
  const [responseDeadline, setResponseDeadline] = useState('')
  const [issuingAuthority, setIssuingAuthority] = useState('')
  const [description, setDescription] = useState('')

  // Extraction & Run State
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [extractedMeta, setExtractedMeta] = useState<{
    notice: any
    validation_status?: string
    warnings?: string[]
    is_scanned?: boolean
    ocr_required?: boolean
  } | null>(null)
  const [investigationId, setInvestigationId] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  const uploadSuccess = uploadStage === 'extracted' && Boolean(investigationId)

  useEffect(() => {
    async function loadClients() {
      try {
        const res = await api.get('/clients')
        if (res.data.success && res.data.data.length > 0) {
          setClients(res.data.data)
          const first = res.data.data[0]
          setClientId(first.id)
          setTaxpayerName(first.business_name || '')
        }
      } catch (e) {
        console.error('Failed to load clients', e)
      }
    }
    loadClients()
  }, [])

  const handleClientChange = (newClientId: string) => {
    setClientId(newClientId)
    const matched = clients.find((c) => c.id === newClientId)
    if (matched) {
      setTaxpayerName(matched.business_name || '')
    }
  }

  const handleFileSelect = (selectedFile: File | null, validationErr: string | null) => {
    setFile(selectedFile)
    setUploadError(validationErr)
    setStartError(null)
    if (!selectedFile) {
      setUploadStage('idle')
      setUploadProgress(0)
    }
  }

  const handleLedgerFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setLedgerFiles(Array.from(e.target.files))
    }
  }

  const validateFields = (): boolean => {
    const errs: FieldErrors = {}
    const trimmedGstin = gstin.trim().toUpperCase()

    if (!trimmedGstin) {
      errs.gstin = 'GSTIN is required (15 characters).'
    } else if (!GSTIN_REGEX.test(trimmedGstin)) {
      errs.gstin = 'Invalid 15-character GSTIN format (e.g. 27AABCT1234C1Z5).'
    }

    if (!noticeNumber.trim()) {
      errs.noticeNumber = 'Notice reference number is required.'
    }

    if (!noticeType.trim()) {
      errs.noticeType = 'Notice type is required (e.g. DRC-01A, ASMT-10).'
    }

    if (!taxPeriod.trim()) {
      errs.taxPeriod = 'Tax period is required (e.g. 2023-11).'
    }

    const parsedAmt = Number(mismatchAmount)
    if (!mismatchAmount.trim() || Number.isNaN(parsedAmt) || parsedAmt < 0) {
      errs.mismatchAmount = 'Enter a valid non-negative mismatch amount.'
    }

    if (responseDeadline && !/^\d{4}-\d{2}-\d{2}$/.test(responseDeadline.trim())) {
      errs.responseDeadline = 'Use YYYY-MM-DD date format.'
    }

    setFieldErrors(errs)
    return Object.keys(errs).length === 0
  }

  const applyExtractedNotice = (notice: any, payload: any) => {
    setExtractedMeta({
      notice,
      validation_status: payload.validation_status,
      warnings: payload.warnings || [],
      is_scanned: payload.is_scanned,
      ocr_required: payload.ocr_required,
    })

    if (notice) {
      if (notice.gstin) {
        const cleanGstin = String(notice.gstin).toUpperCase()
        setGstin(cleanGstin)
        const matchedClient = clients.find(
          (c) => c.primary_gstin?.toUpperCase() === cleanGstin
        )
        if (matchedClient) {
          setClientId(matchedClient.id)
          setTaxpayerName(matchedClient.business_name || '')
        }
      }
      if (notice.notice_number) setNoticeNumber(notice.notice_number)
      if (notice.tax_period) {
        setTaxPeriod(notice.tax_period)
        const fy = deriveFinancialYear(notice.tax_period)
        if (fy) setFinancialYear(fy)
      }
      if (notice.notice_type) {
        setNoticeType(notice.notice_type)
        if (!noticeSection) {
          if (notice.notice_type.includes('DRC-01')) setNoticeSection('Section 73 / 74 CGST Act')
          else if (notice.notice_type.includes('ASMT-10')) setNoticeSection('Section 61 CGST Act')
        }
      }
      if (notice.itc_mismatch !== null && notice.itc_mismatch !== undefined) {
        setMismatchAmount(String(notice.itc_mismatch))
      }
      if (notice.response_deadline) {
        setResponseDeadline(String(notice.response_deadline).slice(0, 10))
      }
      if (notice.issuing_authority) {
        setIssuingAuthority(notice.issuing_authority)
      }
      if (!taxType) {
        setTaxType('CGST / SGST / IGST (ITC)')
      }
      if (!description && notice.notice_number) {
        setDescription(
          `GST Notice Investigation — ${notice.notice_type || 'Notice'} ${notice.notice_number}`
        )
      }
    }
  }

  const handleUploadAndExtract = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setUploadError(null)
    setStartError(null)
    setFieldErrors({})

    if (activeTab === 'FILE' && !file) {
      setUploadError('Please select a GST notice PDF file to upload.')
      return
    }
    if (activeTab === 'TEXT') {
      if (!noticeText.trim()) {
        setUploadError('Please paste the statutory GST notice text.')
        return
      }
      if (!clientId) {
        setUploadError('Please select a registered taxpayer / client first.')
        return
      }
    }

    setSubmitting(true)
    setUploadProgress(0)
    setUploadStage(activeTab === 'FILE' ? 'uploading' : 'extracting')

    try {
      if (activeTab === 'FILE' && file) {
        const formData = new FormData()
        formData.append('file', file)
        if (clientId) formData.append('client_id', clientId)

        const res = await api.post('/notices/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              setUploadProgress(pct)
              if (pct >= 100) {
                setUploadStage('extracting')
              }
            }
          },
        })

        if (res.data?.success && res.data?.data) {
          const payload = res.data.data
          const notice = payload.notice
          setInvestigationId(payload.investigation_id)
          applyExtractedNotice(notice, payload)
          setUploadStage('extracted')
        } else {
          setUploadStage('error')
          setUploadError('Notice extraction returned an unexpected response.')
        }
      } else {
        const invRes = await api.post('/investigations', {
          client_id: clientId,
          title: description.trim() || `GST Notice Investigation - ${noticeNumber || 'DRC-01A'}`,
          description: description.trim() || 'Manual notice text entry',
          tax_period: taxPeriod.trim() || undefined,
          mismatch_amount: mismatchAmount ? parseFloat(mismatchAmount) : undefined,
          response_deadline: responseDeadline.trim() || undefined,
        })

        if (invRes.data?.success && invRes.data?.data) {
          const invId = invRes.data.data.id
          setInvestigationId(invId)

          const noticeForm = new FormData()
          noticeForm.append('notice_text', noticeText)
          await api.post(`/investigations/${invId}/notice`, noticeForm, {
            headers: { 'Content-Type': 'multipart/form-data' },
          })

          setExtractedMeta({
            notice: {
              gstin,
              notice_number: noticeNumber,
              tax_period: taxPeriod,
              notice_type: noticeType,
              itc_mismatch: mismatchAmount ? parseFloat(mismatchAmount) : null,
              response_deadline: responseDeadline || null,
            },
            validation_status: 'PARSED',
            warnings: [],
          })
          setUploadStage('extracted')
        } else {
          setUploadStage('error')
          setUploadError('Failed to create investigation from notice text.')
        }
      }
    } catch (err: any) {
      setUploadStage('error')
      const status = err.response?.status
      const detail = err.response?.data?.detail
      if (status === 401) {
        setUploadError('Authentication expired. Please sign in again.')
      } else if (status === 403) {
        setUploadError('Authorization error: Your account does not have permission to upload notices.')
      } else if (status === 413) {
        setUploadError(detail || 'File exceeds the 15 MB maximum upload limit.')
      } else if (status === 400) {
        setUploadError(detail || 'Invalid notice file or missing client configuration.')
      } else {
        setUploadError(detail || 'Failed to upload and extract notice. Please check backend connectivity and retry.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleStartAiInvestigation = async () => {
    if (!investigationId) return
    setStartError(null)

    if (!validateFields()) {
      setStartError('Please resolve the highlighted validation errors before starting the AI investigation.')
      return
    }

    setSubmitting(true)
    try {
      // Persist any auditor edits supported by PATCH /investigations/{id}
      await api
        .patch(`/investigations/${investigationId}`, {
          title: description.trim() || `GST Notice Investigation - ${noticeNumber}`,
          description: description.trim() || undefined,
          response_deadline: responseDeadline.trim() || undefined,
        })
        .catch(() => {
          // Non-fatal if investigation PATCH isn't required before run
        })

      const idempotencyKey =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `run-${investigationId}-${Date.now()}`

      await api.post(
        `/investigations/${investigationId}/run`,
        {},
        { headers: { 'Idempotency-Key': idempotencyKey } }
      )
      navigate(`/app/auditor/monitoring?id=${investigationId}`)
    } catch (err: any) {
      const status = err.response?.status
      const detail = err.response?.data?.detail
      if (status === 401) {
        setStartError('Authentication expired. Please sign in again to start the investigation.')
      } else if (status === 403) {
        setStartError(detail || 'Authorization error: Only an authorized Auditor can start this AI investigation.')
      } else if (status === 400 || status === 409) {
        setStartError(detail || 'Investigation is not in a valid state to start AI processing.')
      } else if (status >= 500) {
        setStartError('Server error occurred while starting the AI investigation. Please try again.')
      } else {
        setStartError(detail || 'Failed to trigger AI investigation workflow.')
      }
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setUploadStage('idle')
    setUploadProgress(0)
    setExtractedMeta(null)
    setInvestigationId(null)
    setFile(null)
    setUploadError(null)
    setStartError(null)
    setFieldErrors({})
    setGstin('')
    setNoticeNumber('')
    setFinancialYear('')
    setTaxPeriod('')
    setNoticeType('')
    setNoticeSection('')
    setTaxType('')
    setMismatchAmount('')
    setResponseDeadline('')
    setIssuingAuthority('')
    setDescription('')
  }

  const currentStep = uploadSuccess ? 2 : file || noticeText.trim() ? 1 : 0

  return (
    <div className="space-y-6 pb-24">
      <PageHeader
        title="New GST Notice Investigation"
        subtitle="Upload a statutory GST notice PDF, verify extracted metadata, and launch multi-agent reconciliation."
        breadcrumbs={[
          { label: 'Auditor', to: '/app/auditor/dashboard' },
          { label: 'New Investigation' },
        ]}
      />

      {(uploadError || startError) && (
        <div
          role="alert"
          className="p-4 rounded-inner bg-danger/12 border border-danger/30 text-[13.5px] text-danger flex flex-col sm:flex-row sm:items-center justify-between gap-3"
        >
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{startError || uploadError}</span>
          </div>
          {uploadStage === 'error' && (
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={() => handleUploadAndExtract()}
              disabled={submitting}
            >
              Retry Extraction
            </Button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left 6 cols: PDF Upload Zone & Document Preview */}
        <GlassCard className="lg:col-span-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-[18px] leading-[24px] font-medium text-txt-primary">
              Notice Document
            </h2>
            <SegmentedControl
              value={activeTab}
              onChange={(val) => {
                setActiveTab(val)
                setUploadError(null)
              }}
              options={[
                { value: 'FILE', label: 'PDF Upload' },
                { value: 'TEXT', label: 'Manual Text' },
              ]}
            />
          </div>

          {activeTab === 'FILE' ? (
            <div className="space-y-4">
              <PdfUploadPreview
                file={file}
                onFileSelect={handleFileSelect}
                stage={uploadStage}
                uploadProgress={uploadProgress}
                validationStatus={extractedMeta?.validation_status}
                warnings={extractedMeta?.warnings}
                isScanned={extractedMeta?.is_scanned}
                ocrRequired={extractedMeta?.ocr_required}
                disabled={submitting}
              />

              {/* Supporting Ledger Files */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[13px] font-medium text-txt-secondary">
                    Supporting Purchase Ledgers (Optional)
                  </span>
                  <button
                    type="button"
                    onClick={() => ledgerInputRef.current?.click()}
                    className="text-[12.5px] font-medium text-brand-orange hover:text-brand-amber"
                  >
                    + Attach CSV / XLSX
                  </button>
                  <input
                    ref={ledgerInputRef}
                    type="file"
                    multiple
                    accept=".csv,.xlsx,.xls,.json"
                    onChange={handleLedgerFiles}
                    className="hidden"
                  />
                </div>
                {ledgerFiles.length > 0 && (
                  <div className="space-y-2">
                    {ledgerFiles.map((lf, idx) => (
                      <div
                        key={`${lf.name}-${idx}`}
                        className="flex items-center justify-between px-3.5 py-2 rounded-inner bg-surface-2 text-[13px]"
                      >
                        <span className="truncate text-txt-primary font-mono">{lf.name}</span>
                        <button
                          type="button"
                          onClick={() =>
                            setLedgerFiles((prev) => prev.filter((_, i) => i !== idx))
                          }
                          aria-label={`Remove ${lf.name}`}
                          className="text-txt-muted hover:text-danger"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-[13px] font-medium text-txt-secondary mb-2">
                Raw Statutory Notice Text
              </label>
              <textarea
                rows={9}
                value={noticeText}
                onChange={(e) => setNoticeText(e.target.value)}
                placeholder="Paste the complete Form GST DRC-01A or ASMT-10 notice text here..."
                className="w-full rounded-inner bg-surface-2 border border-border-subtle p-4 text-[14px] text-txt-primary placeholder:text-txt-muted focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40 font-mono"
              />
            </div>
          )}

          {/* Extracted Preview Summary when parsed */}
          {uploadSuccess && extractedMeta?.notice && (
            <div className="p-4 rounded-inner bg-accent-mint/8 border border-accent-mint/25 space-y-2.5">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[13px] font-medium text-accent-mint flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  Notice Parsed &amp; Investigation Created
                </span>
                <StatusBadge status={extractedMeta.validation_status || 'PARSED'} />
              </div>
              <div className="grid grid-cols-2 gap-2 text-[12px] pt-1">
                <div>
                  <span className="text-txt-muted block">Investigation ID</span>
                  <span className="font-mono text-txt-secondary truncate block">{investigationId}</span>
                </div>
                <div>
                  <span className="text-txt-muted block">Detected Mismatch</span>
                  <span className="font-semibold tabular-nums text-txt-primary">
                    {extractedMeta.notice.itc_mismatch != null
                      ? formatCurrency(extractedMeta.notice.itc_mismatch)
                      : 'Not detected (enter manually)'}
                  </span>
                </div>
                {extractedMeta.notice.itc_claimed != null && (
                  <div>
                    <span className="text-txt-muted block">ITC Claimed (3B)</span>
                    <span className="tabular-nums text-txt-secondary">
                      {formatCurrency(extractedMeta.notice.itc_claimed)}
                    </span>
                  </div>
                )}
                {extractedMeta.notice.itc_available != null && (
                  <div>
                    <span className="text-txt-muted block">ITC Available (2B)</span>
                    <span className="tabular-nums text-txt-secondary">
                      {formatCurrency(extractedMeta.notice.itc_available)}
                    </span>
                  </div>
                )}
              </div>
              {extractedMeta.notice.extraction_confidence != null && (
                <div className="text-[11.5px] text-txt-muted pt-1 border-t border-white/5 flex items-center justify-between">
                  <span>Parser Confidence</span>
                  <span className="font-mono text-accent-mint tabular-nums">
                    {Math.round(extractedMeta.notice.extraction_confidence * 100)}%
                  </span>
                </div>
              )}
            </div>
          )}
        </GlassCard>

        {/* Right 6 cols: Extraction Stepper & Editable Notice Metadata */}
        <GlassCard className="lg:col-span-6 space-y-5">
          {/* Extraction Stepper */}
          <div className="flex items-center justify-between gap-2 pb-4 border-b border-border-subtle">
            {[
              { step: 0, label: '1. Notice Intake' },
              { step: 1, label: '2. Verify Fields' },
              { step: 2, label: '3. Ready for AI' },
            ].map((item) => {
              const done = currentStep > item.step
              const active = currentStep === item.step
              return (
                <div key={item.step} className="flex items-center gap-2">
                  <span
                    className={`w-6 h-6 rounded-full text-[12px] font-semibold flex items-center justify-center ${
                      done
                        ? 'bg-accent-mint text-[#0F0703]'
                        : active
                        ? 'bg-brand-orange text-white'
                        : 'bg-surface-2 text-txt-muted'
                    }`}
                  >
                    {done ? '✓' : item.step + 1}
                  </span>
                  <span
                    className={`text-[13px] font-medium ${
                      active || done ? 'text-txt-primary' : 'text-txt-muted'
                    }`}
                  >
                    {item.label}
                  </span>
                </div>
              )
            })}
          </div>

          <div className="space-y-4">
            <div>
              <label
                htmlFor="client-select"
                className="block text-[13px] font-medium text-txt-secondary mb-2"
              >
                Registered Taxpayer / Client
              </label>
              <div className="relative">
                <Building2 className="w-4 h-4 text-txt-muted absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                <select
                  id="client-select"
                  value={clientId}
                  onChange={(e) => handleClientChange(e.target.value)}
                  className="w-full h-[48px] pl-11 pr-4 rounded-inner bg-surface-2 border border-border-subtle text-[14.5px] text-txt-primary focus:outline-none focus:border-brand-orange/70 focus:ring-2 focus:ring-brand-orange/40"
                >
                  {clients.length === 0 ? (
                    <option value="">Default Organization Client</option>
                  ) : (
                    clients.map((c) => (
                      <option key={c.id} value={c.id} className="bg-elevated text-txt-primary">
                        {c.business_name} ({c.primary_gstin})
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                id="taxpayer-name"
                label="Taxpayer Name"
                value={taxpayerName}
                onChange={(e) => setTaxpayerName(e.target.value)}
                placeholder="Extracted or client name"
              />
              <Input
                id="notice-gstin"
                label="GSTIN *"
                value={gstin}
                onChange={(e) => {
                  setGstin(e.target.value.toUpperCase())
                  if (fieldErrors.gstin) setFieldErrors((p) => ({ ...p, gstin: undefined }))
                }}
                placeholder="e.g. 27AABCT1234C1Z5"
                error={fieldErrors.gstin}
                className="font-mono tabular-nums uppercase"
              />
              <Input
                id="notice-number"
                label="Notice Number *"
                value={noticeNumber}
                onChange={(e) => {
                  setNoticeNumber(e.target.value)
                  if (fieldErrors.noticeNumber) setFieldErrors((p) => ({ ...p, noticeNumber: undefined }))
                }}
                placeholder="e.g. ZA271223001928K"
                error={fieldErrors.noticeNumber}
                className="font-mono tabular-nums"
              />
              <Input
                id="financial-year"
                label="Financial Year"
                value={financialYear}
                onChange={(e) => setFinancialYear(e.target.value)}
                placeholder="e.g. 2023-24"
                className="font-mono tabular-nums"
              />
              <Input
                id="tax-period"
                label="Tax Period *"
                value={taxPeriod}
                onChange={(e) => {
                  setTaxPeriod(e.target.value)
                  if (fieldErrors.taxPeriod) setFieldErrors((p) => ({ ...p, taxPeriod: undefined }))
                }}
                placeholder="e.g. 2023-11"
                error={fieldErrors.taxPeriod}
                className="font-mono tabular-nums"
              />
              <Input
                id="notice-type"
                label="Notice Type *"
                value={noticeType}
                onChange={(e) => {
                  setNoticeType(e.target.value)
                  if (fieldErrors.noticeType) setFieldErrors((p) => ({ ...p, noticeType: undefined }))
                }}
                placeholder="e.g. DRC-01A, ASMT-10"
                error={fieldErrors.noticeType}
              />
              <Input
                id="notice-section"
                label="Section / Provision"
                value={noticeSection}
                onChange={(e) => setNoticeSection(e.target.value)}
                placeholder="e.g. Section 73 CGST Act"
              />
              <Input
                id="tax-type"
                label="Tax Type"
                value={taxType}
                onChange={(e) => setTaxType(e.target.value)}
                placeholder="e.g. CGST / SGST / IGST"
              />
              <Input
                id="mismatch-amount"
                label="Alleged Mismatch Amount (₹) *"
                type="number"
                value={mismatchAmount}
                onChange={(e) => {
                  setMismatchAmount(e.target.value)
                  if (fieldErrors.mismatchAmount) setFieldErrors((p) => ({ ...p, mismatchAmount: undefined }))
                }}
                placeholder="0.00"
                error={fieldErrors.mismatchAmount}
                className="font-mono tabular-nums"
              />
              <Input
                id="response-deadline"
                label="Response Deadline"
                type="date"
                value={responseDeadline}
                onChange={(e) => {
                  setResponseDeadline(e.target.value)
                  if (fieldErrors.responseDeadline) setFieldErrors((p) => ({ ...p, responseDeadline: undefined }))
                }}
                error={fieldErrors.responseDeadline}
                className="font-mono tabular-nums"
              />
            </div>

            {issuingAuthority && (
              <Input
                id="issuing-authority"
                label="Issuing Authority"
                value={issuingAuthority}
                onChange={(e) => setIssuingAuthority(e.target.value)}
              />
            )}

            <Input
              id="case-description"
              label="Investigation Title / Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="ITC Mismatch between GSTR-3B and GSTR-2B"
            />
          </div>
        </GlassCard>
      </div>

      {/* Sticky Footer Action Bar */}
      <div className="sticky bottom-4 z-30">
        <GlassCard elevated padding="sm" className="px-6 py-4 border-border-strong flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="text-[13.5px] text-txt-secondary">
            {uploadSuccess ? (
              <span className="text-accent-mint font-medium">
                Notice extracted. Verify fields above and launch the 6-agent investigation pipeline.
              </span>
            ) : (
              <span>Upload &amp; extract notice metadata from your PDF before starting the AI pipeline.</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {uploadSuccess && (
              <Button variant="secondary" onClick={handleReset} disabled={submitting} leftIcon={<RotateCcw className="w-4 h-4" />}>
                Reset
              </Button>
            )}
            {!uploadSuccess ? (
              <Button
                variant="primary"
                loading={submitting}
                onClick={() => handleUploadAndExtract()}
                leftIcon={<Upload className="w-4 h-4" />}
              >
                {submitting ? 'Extracting Notice...' : 'Upload & Extract Notice'}
              </Button>
            ) : (
              <Button
                variant="primary"
                loading={submitting}
                onClick={handleStartAiInvestigation}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                {submitting ? 'Starting AI Pipeline...' : 'Start AI Investigation'}
              </Button>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
