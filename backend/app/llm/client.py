import os
import json
import socket
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger("llm_client")

def _is_host_reachable(host: str, port: int = 443, timeout: float = 0.5) -> bool:
    """Fast check whether an external LLM endpoint is reachable before blocking async calls."""
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

class LLMResponse(BaseModel):
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    usage: LLMUsage = LLMUsage()
    model: str = settings.groq_model
    is_mock: bool = False

class LLMClient:
    """
    Enterprise LLM Client with dual support for:
    1. Groq API (model: llama-3.1-8b-instant) via high-speed OpenAI-compatible endpoints
    2. Google Gemini API
    3. Deterministic Mock Adapter fallback for offline / sandboxed environments.
    """
    def __init__(self):
        self.groq_api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self.gemini_api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        
        # Determine active key & provider
        if self.groq_api_key and self.groq_api_key.startswith("gsk_"):
            self.provider = "groq"
            self.api_key = self.groq_api_key
            self.model = settings.groq_model or "llama-3.1-8b-instant"
        elif self.gemini_api_key and self.gemini_api_key.startswith("gsk_"):
            self.provider = "groq"
            self.api_key = self.gemini_api_key
            self.model = "llama-3.1-8b-instant"
        else:
            self.provider = "gemini"
            self.api_key = self.gemini_api_key
            self.model = settings.gemini_model or "gemini-2.0-flash"

    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        mock_response: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Invoke Groq (llama-3.1-8b-instant) or Gemini API with structured JSON output support.
        Falls back seamlessly to Mock Adapter if API key is not configured, DNS fails, or offline.
        """
        # 1. Attempt Groq API if active key is Groq (starts with gsk_)
        if self.api_key and self.api_key.startswith("gsk_"):
            if _is_host_reachable("api.groq.com", 443):
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    messages = []
                    if system_instruction:
                        messages.append({"role": "system", "content": system_instruction})
                    messages.append({"role": "user", "content": prompt})

                    payload: Dict[str, Any] = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 2048
                    }
                    if schema or "json" in prompt.lower() or "json" in (system_instruction or "").lower():
                        payload["response_format"] = {"type": "json_object"}

                    # Try requested model, and fallback to available models on Groq if 404
                    models_to_try = [self.model, "openai/gpt-oss-20b"] if self.model != "openai/gpt-oss-20b" else ["openai/gpt-oss-20b"]
                    res = None
                    for m in models_to_try:
                        payload["model"] = m
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            res = await client.post(url, headers=headers, json=payload)
                            if res.status_code == 200:
                                break

                    if res and res.status_code == 200:
                        data = res.json()
                        candidate = data["choices"][0]["message"]["content"]
                        usage_meta = data.get("usage", {})
                        p_tokens = usage_meta.get("prompt_tokens", 0)
                        c_tokens = usage_meta.get("completion_tokens", 0)
                        t_tokens = usage_meta.get("total_tokens", p_tokens + c_tokens)
                        
                        # Groq model pricing (~$0.05/1M prompt, $0.08/1M completion)
                        cost = (p_tokens * 0.00000005) + (c_tokens * 0.00000008)
                        
                        structured = None
                        try:
                            structured = json.loads(candidate)
                        except Exception:
                            pass

                        return LLMResponse(
                            content=candidate,
                            structured_data=structured,
                            usage=LLMUsage(
                                prompt_tokens=p_tokens,
                                completion_tokens=c_tokens,
                                total_tokens=t_tokens,
                                estimated_cost_usd=cost
                            ),
                            model=payload.get("model", self.model),
                            is_mock=False
                        )
                except Exception as e:
                    logger.warning("groq_api_call_failed_falling_back_to_mock", error=str(e))
            else:
                logger.info("groq_host_unreachable_using_mock_adapter")

        # 2. Attempt Gemini API if non-placeholder key is available
        elif self.api_key and self.api_key not in ("PLACEHOLDER-SET-IN-ENV", "your-gemini-api-key-here", ""):
            if _is_host_reachable("generativelanguage.googleapis.com", 443):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                    contents = [{"parts": [{"text": prompt}]}]
                    payload = {"contents": contents}
                    
                    if system_instruction:
                        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

                    generation_config: Dict[str, Any] = {"temperature": 0.1, "maxOutputTokens": settings.gemini_max_tokens}
                    if schema:
                        generation_config["responseMimeType"] = "application/json"
                        generation_config["responseSchema"] = schema
                    payload["generationConfig"] = generation_config

                    async with httpx.AsyncClient(timeout=10.0) as client:
                        res = await client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            candidate = data["candidates"][0]["content"]["parts"][0]["text"]
                            metadata = data.get("usageMetadata", {})
                            p_tokens = metadata.get("promptTokenCount", 0)
                            c_tokens = metadata.get("candidatesTokenCount", 0)
                            t_tokens = metadata.get("totalTokenCount", p_tokens + c_tokens)
                            cost = (p_tokens * 0.0000001) + (c_tokens * 0.0000004)
                            
                            structured = None
                            if schema:
                                try:
                                    structured = json.loads(candidate)
                                except Exception:
                                    pass

                            return LLMResponse(
                                content=candidate,
                                structured_data=structured,
                                usage=LLMUsage(
                                    prompt_tokens=p_tokens,
                                    completion_tokens=c_tokens,
                                    total_tokens=t_tokens,
                                    estimated_cost_usd=cost
                                ),
                                model=self.model,
                                is_mock=False
                            )
                except Exception as e:
                    logger.warning("gemini_api_call_failed_falling_back_to_mock", error=str(e))
            else:
                logger.info("gemini_host_unreachable_using_mock_adapter")

        # 3. Deterministic Mock Adapter Fallback
        return self._generate_mock_response(prompt, system_instruction, mock_response)

    def _generate_mock_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        mock_response: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Deterministic Mock Adapter for offline verification and testing."""
        if mock_response:
            return LLMResponse(
                content=json.dumps(mock_response),
                structured_data=mock_response,
                usage=LLMUsage(prompt_tokens=150, completion_tokens=220, total_tokens=370, estimated_cost_usd=0.00002),
                model="llama-3.1-8b-instant-mock",
                is_mock=True
            )

        # Context-aware mock responses
        p_lower = prompt.lower()
        if "notice parser" in (system_instruction or "").lower() or "drc-01a" in p_lower:
            data = {
                "notice_number": "ZA271223001928K",
                "notice_type": "DRC-01A",
                "gstin": "27AABCT1234C1Z5",
                "tax_period": "2023-11",
                "itc_claimed": 174600.0,
                "itc_available": 93600.0,
                "itc_mismatch": 81000.0,
                "response_deadline": "2024-01-15",
                "issued_date": "2023-12-28",
                "issuing_authority": "Deputy Commissioner of State Tax, Circle-5, Mumbai",
                "extraction_confidence": 0.98,
                "uncertain_fields": []
            }
        elif "root cause" in (system_instruction or "").lower():
            data = {
                "hypotheses": [
                    {
                        "type": "TIMING_DIFFERENCE",
                        "title": "Supplier GSTR-1 Filed in Subsequent Tax Period",
                        "description": "Supplier Apex Logistics issued invoice in Nov 2023 but reported in Dec 2023 GSTR-1.",
                        "confidence": 0.95
                    },
                    {
                        "type": "DUPLICATE_INVOICE",
                        "title": "Potential Duplicate Invoice Booking",
                        "description": "Invoice booked multiple times in purchase register.",
                        "confidence": 0.15
                    }
                ]
            }
        elif "response drafter" in (system_instruction or "").lower():
            data = {
                "statutory_provisions": ["Section 16(2) CGST Act, 2017", "Circular No. 183/15/2022-GST"],
                "executive_summary": "The alleged discrepancy of INR 81,000 arises purely on account of a timing difference in supplier reporting under GSTR-1, which has since been fully rectified.",
                "response_body": "Sir/Madam, With reference to the DRC-01A intimation dated 28-Dec-2023 regarding alleged excess ITC of INR 81,000 for Nov 2023, we respectfully submit that the credit relates to Invoice INV-2023-0891 from Apex Logistics Services Pvt Ltd. The supplier filed their GSTR-1 on 11-Jan-2024 (ARN AA271223999912A) reflecting the invoice in GSTR-2B for Dec 2023. Under Section 16(2), all conditions for ITC availment were fully satisfied by the taxpayer. Since tax has been discharged to the government, there is no loss of revenue. We pray that the proposed demand be dropped.",
                "verified_claims": ["INV-2023-0891 tax paid and reflected in Dec 2023 GSTR-2B"]
            }
        else:
            data = {"status": "SUCCESS", "analysis": "Analysis generated by TaxPilot AI model adapter"}

        return LLMResponse(
            content=json.dumps(data),
            structured_data=data,
            usage=LLMUsage(prompt_tokens=200, completion_tokens=300, total_tokens=500, estimated_cost_usd=0.00003),
            model="llama-3.1-8b-instant-mock",
            is_mock=True
        )

# Maintain backward compatibility for imports
GeminiClient = LLMClient
llm_client = LLMClient()
