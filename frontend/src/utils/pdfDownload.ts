import { api } from '@/services/api/client'

async function extractErrorFromBlob(blob: Blob): Promise<string | null> {
  try {
    const text = await blob.text()
    if (!text) return null
    const parsed = JSON.parse(text)
    return parsed?.detail || parsed?.message || text
  } catch {
    return null
  }
}

export async function extractApiErrorMessage(err: any, fallback: string): Promise<string> {
  const data = err?.response?.data
  if (data instanceof Blob) {
    const parsed = await extractErrorFromBlob(data)
    if (parsed) return parsed
  }
  if (typeof data?.detail === 'string' && data.detail) return data.detail
  if (typeof data?.message === 'string' && data.message) return data.message
  if (typeof err?.message === 'string' && err.message) return err.message
  return fallback
}

function parseFilenameFromDisposition(disposition?: string): string | null {
  if (!disposition) return null
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utfMatch?.[1]) return decodeURIComponent(utfMatch[1].trim())
  const match = disposition.match(/filename="?([^";]+)"?/i)
  return match?.[1]?.trim() || null
}

/**
 * Downloads the final approved PDF report from `/api/v1/reports/{id}/download`,
 * validates that the response is a non-empty `%PDF-` document, extracts the
 * server-provided filename (or constructs one from noticeNumber / id), and
 * surfaces real backend error messages when Axios returns an error Blob.
 */
export async function downloadReportPdf(
  investigationId: string,
  noticeNumber?: string | null
): Promise<string> {
  const res = await api.get(`/reports/${investigationId}/download`, {
    responseType: 'blob',
  })

  const blob =
    res.data instanceof Blob
      ? res.data
      : new Blob([res.data], { type: 'application/pdf' })

  if (blob.size === 0) {
    throw new Error('Server returned an empty PDF response (0 bytes).')
  }

  const contentType = String(res.headers?.['content-type'] || '').toLowerCase()
  if (contentType.includes('application/json') || contentType.includes('text/html')) {
    const msg = await extractErrorFromBlob(blob)
    throw new Error(msg || `Unexpected response content-type: ${contentType}`)
  }

  // Verify %PDF- magic header
  const headerBytes = new Uint8Array(await blob.slice(0, 5).arrayBuffer())
  const headerStr = String.fromCharCode(...headerBytes)
  if (headerStr !== '%PDF-') {
    const maybeErr = await extractErrorFromBlob(blob)
    throw new Error(maybeErr || 'Downloaded file is not a valid PDF document.')
  }

  const serverFilename = parseFilenameFromDisposition(res.headers?.['content-disposition'])
  const safeNotice = noticeNumber ? noticeNumber.replace(/[^a-zA-Z0-9_-]/g, '_') : investigationId.slice(0, 8)
  const filename = serverFilename || `TaxPilot_Final_Report_${safeNotice}.pdf`

  const pdfBlob = new Blob([blob], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(pdfBlob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()

  // Delay revocation so the browser finishes reading the blob URL
  window.setTimeout(() => {
    window.URL.revokeObjectURL(url)
  }, 1000)

  return filename
}
