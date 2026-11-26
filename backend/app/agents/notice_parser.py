import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from app.llm.client import llm_client
from app.config.logging import get_logger

logger = get_logger("notice_parser_agent")

class ExtractedNoticeData(BaseModel):
    notice_number: Optional[str] = None
    notice_type: Optional[str] = None
    gstin: Optional[str] = None
    tax_period: Optional[str] = None
    itc_claimed: Optional[float] = None
    itc_available: Optional[float] = None
    itc_mismatch: Optional[float] = None
    response_deadline: Optional[str] = None
    issued_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    extraction_confidence: float = 0.0
    uncertain_fields: List[str] = []
    raw_text: str = ""

class NoticeParserAgent:
    """Agent 2 — Notice Parser Agent with deterministic validation and structured Pydantic output."""
    def __init__(self):
        self.role_name = "Notice Parser Agent"

    async def parse_text(self, text: str) -> ExtractedNoticeData:
        logger.info("notice_parser_started", text_length=len(text))
        
        t_lower = text.lower()
        has_gst_identifiers = any(k in t_lower for k in ["gstin", "drc-01", "gstr-", "gstr1", "gstr2", "gstr3", "input tax credit", "form gst"])
        
        if not has_gst_identifiers or len(text.strip()) < 30:
            return ExtractedNoticeData(
                notice_number=None,
                notice_type=None,
                gstin=None,
                tax_period=None,
                itc_claimed=None,
                itc_available=None,
                itc_mismatch=None,
                extraction_confidence=0.0,
                uncertain_fields=["notice_number", "gstin", "tax_period", "itc_mismatch"],
                raw_text=text
            )

        # Precise regex extraction for official Indian GST notices
        # Notice Type
        notice_type = "DRC-01A"
        nt_match = re.search(r"\b(DRC-01[A-D]?|DRC-07|ASMT-10)\b", text, re.IGNORECASE)
        if nt_match:
            notice_type = nt_match.group(1).upper()

        # Notice Number
        notice_num = None
        n_match = re.search(r"(?:notice\s+(?:number|no|ref|id)|reference(?:\s+(?:number|no|ref|id))?\.?)[^\w/]*\s*([A-Z0-9][A-Z0-9/\-]{6,30})", text, re.IGNORECASE)
        if n_match:
            notice_num = n_match.group(1).strip()
        else:
            za_match = re.search(r"\b(ZA[0-9]{10}[A-Z0-9]{1,4})\b", text)
            if za_match:
                notice_num = za_match.group(1).strip()

        # GSTIN
        gstin = None
        g_match = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
        if g_match:
            gstin = g_match.group(1).strip()

        # Tax Period
        MONTHS = {
            "january": "01", "jan": "01", "february": "02", "feb": "02",
            "march": "03", "mar": "03", "april": "04", "apr": "04",
            "may": "05", "june": "06", "jun": "06", "july": "07", "jul": "07",
            "august": "08", "aug": "08", "september": "09", "sep": "09",
            "october": "10", "oct": "10", "november": "11", "nov": "11",
            "december": "12", "dec": "12"
        }
        period = None
        p_match = re.search(r"\b(20[2-3][0-9]-[0-1][0-9])\b", text)
        if p_match:
            period = p_match.group(1).strip()
        else:
            tp_match = re.search(r"tax\s+period[^\n\r]*?\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(20[2-3][0-9])\b", text, re.IGNORECASE)
            mp_match = tp_match or re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,\s]+(20[2-3][0-9])\b", text, re.IGNORECASE)
            if mp_match:
                period = f"{mp_match.group(2)}-{MONTHS[mp_match.group(1).lower()]}"

        # Amounts: Claimed, Available, Mismatch
        claimed = None
        avail = None
        mismatch = None

        # Table-first matching for claimed
        c_match = re.search(r"(?:itc\s+claimed|claimed\s+as\s+per)[^\n\r]*\n\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if not c_match:
            lines = [l for l in text.splitlines() if "exceed" not in l.lower()]
            clean_text = "\n".join(lines)
            c_match = re.search(r"(?:itc\s+claimed|claimed\s+in\s+gstr-?3b)[^\n\r\d]*?(?:INR|Rs\.?|₹)?\s*[:\s]\s*([\d,]+(?:\.\d{2})?)", clean_text, re.IGNORECASE)
        if c_match:
            try:
                claimed = float(c_match.group(1).replace(",", ""))
            except Exception:
                pass

        # Table-first matching for available
        a_match = re.search(r"(?:itc\s+available|available\s+as\s+per)[^\n\r]*\n\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if not a_match:
            lines = [l for l in text.splitlines() if "exceed" not in l.lower()]
            clean_text = "\n".join(lines)
            a_match = re.search(r"(?:itc\s+available|available\s+in\s+gstr-?2b)[^\n\r\d]*?(?:INR|Rs\.?|₹)?\s*[:\s]\s*([\d,]+(?:\.\d{2})?)", clean_text, re.IGNORECASE)
        if a_match:
            try:
                avail = float(a_match.group(1).replace(",", ""))
            except Exception:
                pass

        pat_mismatch = r"(?:exceeds[^\n\r]*?by\s+(?:INR|Rs\.?|₹|I)?\s*|disputed\s+amount\s*\n\s*(?:INR|Rs\.?|₹|I)?\s*|(?:excess\s+itc\s+claimed|total\s+mismatch|difference|discrepancy(?:\s+amount)?(?:\s+of)?)[^\n\r]*?(?:INR|Rs\.?|₹)\s*|(?:difference|mismatch)\s*\n\s*)([\d,]+(?:\.\d{2})?)"
        m_match = re.search(pat_mismatch, text, re.IGNORECASE)
        if m_match:
            try:
                mismatch = float(m_match.group(1).replace(",", ""))
            except Exception:
                pass

        prompt = f"""You are the Notice Parser Agent in TaxPilot AI.
Extract structured fields from this Indian GST notice text.
CRITICAL RULE: NEVER invent or hallucinate missing values. If a field is not explicitly present, return null.

Notice text:
\"\"\"
{text}
\"\"\"

Return a valid JSON object matching this schema:
{{
  "notice_number": string or null,
  "notice_type": string or null,
  "gstin": string or null,
  "tax_period": string or null,
  "itc_claimed": float or null,
  "itc_available": float or null,
  "itc_mismatch": float or null,
  "response_deadline": string (YYYY-MM-DD) or null,
  "issued_date": string (YYYY-MM-DD) or null,
  "issuing_authority": string or null,
  "extraction_confidence": float,
  "uncertain_fields": [string]
}}"""

        system_instruction = "You are a professional Notice Parser Agent in TaxPilot AI. Return only strict JSON."
        llm_res = await llm_client.generate_content(prompt=prompt, system_instruction=system_instruction)
        data = llm_res.structured_data or {}

        # Ground truth regex overrides
        if gstin:
            data["gstin"] = gstin
        if notice_num:
            data["notice_number"] = notice_num
        if notice_type:
            data["notice_type"] = notice_type
        if claimed is not None:
            data["itc_claimed"] = claimed
        if avail is not None:
            data["itc_available"] = avail
        if mismatch is not None:
            data["itc_mismatch"] = mismatch
        if period:
            data["tax_period"] = period

        # Check claimed vs available arithmetic
        if data.get("itc_claimed") is not None and data.get("itc_available") is not None and data.get("itc_mismatch") is None:
            data["itc_mismatch"] = round(float(data["itc_claimed"]) - float(data["itc_available"]), 2)

        data["raw_text"] = text
        return ExtractedNoticeData(**data)
