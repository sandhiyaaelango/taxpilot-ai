import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from app.mcp.contracts.schemas import (
    GetNoticeInput, NoticeDetailOutput,
    GetFiledReturnsInput, GetFiledReturnsOutput, FiledReturnSummary,
    GetReturnDetailsInput, GetReturnDetailsOutput, ReturnLineItem,
    GetVendorFilingStatusInput, GetVendorFilingStatusOutput
)

app = FastAPI(
    title="Tax Portal MCP Server",
    description="Simulated GST Portal MCP Server for TaxPilot AI",
    version="1.0.0"
)

# Realistic Synthetic GST Portal Mock Dataset
MOCK_NOTICES = {
    "ZA271223001928K": {
        "source_id": "NOT-ZA271223001928K",
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
        "discrepancy_details": [
            {
                "rule": "Rule 36(4)",
                "description": "Excess ITC claimed in Table 4(A)(5) of GSTR-3B over GSTR-2B auto-drafted statement",
                "mismatch_cgst": 40500.0,
                "mismatch_sgst": 40500.0,
                "mismatch_igst": 0.0,
                "mismatch_total": 81000.0
            }
        ]
    },
    "TXP/DRC01A/2026/000184": {
        "source_id": "NOT-TXP-2026-000184",
        "notice_number": "TXP/DRC01A/2026/000184",
        "notice_type": "DRC-01A",
        "gstin": "33AABCA1234F1Z5",
        "tax_period": "2026-11",
        "itc_claimed": 1620000.0,
        "itc_available": 1480000.0,
        "itc_mismatch": 140000.0,
        "response_deadline": "2026-12-31",
        "issued_date": "2026-11-18",
        "issuing_authority": "Assistant Commissioner of Central Tax, Division-I, Chennai",
        "discrepancy_details": [
            {
                "rule": "Rule 36(4)",
                "description": "Excess ITC claimed in GSTR-3B over auto-drafted GSTR-2B statement",
                "mismatch_cgst": 35000.0,
                "mismatch_sgst": 35000.0,
                "mismatch_igst": 70000.0,
                "mismatch_total": 140000.0
            }
        ]
    }
}

MOCK_FILED_RETURNS = {
    ("27AABCT1234C1Z5", "2023-11"): [
        {
            "source_id": "RET-3B-202311",
            "return_type": "GSTR-3B",
            "tax_period": "2023-11",
            "arn": "AA271123019827B",
            "filing_date": "2023-12-20",
            "status": "FILED",
            "total_taxable_value": 970000.0,
            "itc_eligible": 174600.0
        },
        {
            "source_id": "RET-2B-202311",
            "return_type": "GSTR-2B",
            "tax_period": "2023-11",
            "arn": "AUTO-2B-202311",
            "filing_date": "2023-12-14",
            "status": "AVAILABLE",
            "total_taxable_value": 520000.0,
            "itc_eligible": 93600.0
        }
    ],
    ("27AABCT1234C1Z5", "2023-12"): [
        {
            "source_id": "RET-2B-202312",
            "return_type": "GSTR-2B",
            "tax_period": "2023-12",
            "arn": "AUTO-2B-202312",
            "filing_date": "2024-01-14",
            "status": "AVAILABLE",
            "total_taxable_value": 450000.0,
            "itc_eligible": 81000.0  # Timing difference reflected here!
        }
    ],
    ("34ABCDE1234F1Z5", "2026-05"): [
        {
            "source_id": "RET-3B-202605",
            "return_type": "GSTR-3B",
            "tax_period": "2026-05",
            "arn": "AA340526019827B",
            "filing_date": "2026-06-20",
            "status": "FILED",
            "total_taxable_value": 20000.0,
            "itc_eligible": 3600.0
        },
        {
            "source_id": "RET-2B-202605",
            "return_type": "GSTR-2B",
            "tax_period": "2026-05",
            "arn": "AUTO-2B-202605",
            "filing_date": "2026-06-14",
            "status": "AVAILABLE",
            "total_taxable_value": 12000.0,
            "itc_eligible": 2160.0
        }
    ],
    ("34ABCDE1234F1Z5", "2026-06"): [
        {
            "source_id": "RET-2B-202606",
            "return_type": "GSTR-2B",
            "tax_period": "2026-06",
            "arn": "AUTO-2B-202606",
            "filing_date": "2026-07-14",
            "status": "AVAILABLE",
            "total_taxable_value": 8000.0,
            "itc_eligible": 1440.0
        }
    ],
    ("33AABCA1234F1Z5", "2026-11"): [
        {
            "source_id": "RET-3B-202611-33",
            "return_type": "GSTR-3B",
            "tax_period": "2026-11",
            "arn": "AA331126019827B",
            "filing_date": "2026-12-20",
            "status": "FILED",
            "total_taxable_value": 9000000.0,
            "itc_eligible": 1620000.0
        },
        {
            "source_id": "RET-2B-202611-33",
            "return_type": "GSTR-2B",
            "tax_period": "2026-11",
            "arn": "AUTO-2B-202611-33",
            "filing_date": "2026-12-14",
            "status": "AVAILABLE",
            "total_taxable_value": 8222222.0,
            "itc_eligible": 1480000.0
        }
    ],
    ("33AABCA1234F1Z5", "2026-12"): [
        {
            "source_id": "RET-2B-202612-33",
            "return_type": "GSTR-2B",
            "tax_period": "2026-12",
            "arn": "AUTO-2B-202612-33",
            "filing_date": "2027-01-14",
            "status": "AVAILABLE",
            "total_taxable_value": 777777.78,
            "itc_eligible": 140000.0  # Timing difference reflected in subsequent 2B
        }
    ],
    ("33AABCA1234F1Z5", "2023-11"): [
        {
            "source_id": "RET-3B-202311-33",
            "return_type": "GSTR-3B",
            "tax_period": "2023-11",
            "arn": "AA331123019827B",
            "filing_date": "2023-12-20",
            "status": "FILED",
            "total_taxable_value": 9000000.0,
            "itc_eligible": 1620000.0
        },
        {
            "source_id": "RET-2B-202311-33",
            "return_type": "GSTR-2B",
            "tax_period": "2023-11",
            "arn": "AUTO-2B-202311-33",
            "filing_date": "2023-12-14",
            "status": "AVAILABLE",
            "total_taxable_value": 8222222.0,
            "itc_eligible": 1480000.0
        }
    ],
    ("33AABCA1234F1Z5", "2023-12"): [
        {
            "source_id": "RET-2B-202312-33",
            "return_type": "GSTR-2B",
            "tax_period": "2023-12",
            "arn": "AUTO-2B-202312-33",
            "filing_date": "2024-01-14",
            "status": "AVAILABLE",
            "total_taxable_value": 777777.78,
            "itc_eligible": 140000.0
        }
    ]
}

MOCK_RETURN_DETAILS = {
    ("27AABCT1234C1Z5", "GSTR-2B", "2023-11"): [
        {
            "source_id": "2B-ITEM-DL8841",
            "invoice_number": "DL-8841",
            "supplier_gstin": "07AAACD7777E1Z3",
            "invoice_date": "2023-11-15",
            "taxable_value": 320000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 57600.0,
            "total_tax": 57600.0,
            "filing_date": "2023-12-11"
        },
        {
            "source_id": "2B-ITEM-SP5501",
            "invoice_number": "SP-5501",
            "supplier_gstin": "27AAACS1111B1Z2",
            "invoice_date": "2023-10-31",
            "taxable_value": 200000.0,
            "cgst": 18000.0,
            "sgst": 18000.0,
            "igst": 0.0,
            "total_tax": 36000.0,
            "filing_date": "2023-11-10"
        }
    ],
    ("27AABCT1234C1Z5", "GSTR-2B", "2023-12"): [
        {
            "source_id": "2B-ITEM-INV0891",
            "invoice_number": "INV-2023-0891",
            "supplier_gstin": "27AABCS5555D1Z8",  # Apex Logistics
            "invoice_date": "2023-11-28",
            "taxable_value": 450000.0,
            "cgst": 40500.0,
            "sgst": 40500.0,
            "igst": 0.0,
            "total_tax": 81000.0,
            "filing_date": "2024-01-11"  # Filed in Dec period on 11-Jan
        }
    ],
    ("34ABCDE1234F1Z5", "GSTR-2B", "2026-06"): [
        {
            "source_id": "2B-ITEM-INV0511",
            "invoice_number": "INV-2026-0511",
            "supplier_gstin": "34XYZAB9876C1Z2",  # Coastal Hardware Supplies
            "invoice_date": "2026-05-18",
            "taxable_value": 8000.0,
            "cgst": 720.0,
            "sgst": 720.0,
            "igst": 0.0,
            "total_tax": 1440.0,
            "filing_date": "2026-07-10"
        }
    ],
    ("33AABCA1234F1Z5", "GSTR-2B", "2026-12"): [
        {
            "source_id": "2B-ITEM-INV0184",
            "invoice_number": "INV-2026-0184",
            "supplier_gstin": "27AABCS5555D1Z8",  # Apex Logistics
            "invoice_date": "2026-11-10",
            "taxable_value": 777777.78,
            "cgst": 35000.0,
            "sgst": 35000.0,
            "igst": 70000.0,
            "total_tax": 140000.0,
            "filing_date": "2027-01-11"
        }
    ],
    ("33AABCA1234F1Z5", "GSTR-2B", "2023-12"): [
        {
            "source_id": "2B-ITEM-INV9941",
            "invoice_number": "INV-2023-9941",
            "supplier_gstin": "27AABCS5555D1Z8",  # Apex Logistics
            "invoice_date": "2023-11-20",
            "taxable_value": 777777.78,
            "cgst": 35000.0,
            "sgst": 35000.0,
            "igst": 70000.0,
            "total_tax": 140000.0,
            "filing_date": "2024-01-11"
        }
    ]
}

MOCK_VENDOR_STATUS = {
    ("27AABCS5555D1Z8", "2026-11"): {
        "source_id": "VEN-APEX-202611",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "tax_period": "2026-11",
        "gstr1_status": "NOT_FILED",
        "gstr1_filing_date": None,
        "gstr1_arn": None,
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2026-12-20",
        "invoices_reported": 0,
        "total_invoice_value": 0.0
    },
    ("27AABCS5555D1Z8", "2026-12"): {
        "source_id": "VEN-APEX-202612",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "tax_period": "2026-12",
        "gstr1_status": "FILED",
        "gstr1_filing_date": "2027-01-11",
        "gstr1_arn": "AA271226999912A",
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2027-01-20",
        "invoices_reported": 1,
        "total_invoice_value": 917777.78
    },
    ("34XYZAB9876C1Z2", "2026-05"): {
        "source_id": "VEN-COASTAL-202605",
        "supplier_gstin": "34XYZAB9876C1Z2",
        "supplier_name": "Coastal Hardware Supplies",
        "tax_period": "2026-05",
        "gstr1_status": "NOT_FILED",
        "gstr1_filing_date": None,
        "gstr1_arn": None,
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2026-06-20",
        "invoices_reported": 0,
        "total_invoice_value": 0.0
    },
    ("34XYZAB9876C1Z2", "2026-06"): {
        "source_id": "VEN-COASTAL-202606",
        "supplier_gstin": "34XYZAB9876C1Z2",
        "supplier_name": "Coastal Hardware Supplies",
        "tax_period": "2026-06",
        "gstr1_status": "FILED",
        "gstr1_filing_date": "2026-07-10",
        "gstr1_arn": "AA340626999912A",
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2026-07-18",
        "invoices_reported": 1,
        "total_invoice_value": 9440.0
    },
    ("27AABCS5555D1Z8", "2023-11"): {
        "source_id": "VEN-APEX-202311",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "tax_period": "2023-11",
        "gstr1_status": "NOT_FILED",
        "gstr1_filing_date": None,
        "gstr1_arn": None,
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2023-12-20",
        "invoices_reported": 0,
        "total_invoice_value": 0.0
    },
    ("27AABCS5555D1Z8", "2023-12"): {
        "source_id": "VEN-APEX-202312",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "tax_period": "2023-12",
        "gstr1_status": "FILED",
        "gstr1_filing_date": "2024-01-11",
        "gstr1_arn": "AA271223999912A",
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2024-01-20",
        "invoices_reported": 1,
        "total_invoice_value": 531000.0
    },
    ("07AAACD7777E1Z3", "2023-11"): {
        "source_id": "VEN-DELTA-202311",
        "supplier_gstin": "07AAACD7777E1Z3",
        "supplier_name": "Delta Electricals India Ltd",
        "tax_period": "2023-11",
        "gstr1_status": "FILED",
        "gstr1_filing_date": "2023-12-10",
        "gstr1_arn": "AA071123112233C",
        "gstr3b_status": "FILED",
        "gstr3b_filing_date": "2023-12-18",
        "invoices_reported": 1,
        "total_invoice_value": 377600.0
    }
}

# MCP Tools Registry definition
TAX_PORTAL_TOOLS = [
    {
        "name": "get_notice",
        "description": "Retrieve comprehensive GST notice details including claimed vs available ITC amounts and discrepancy breakdowns.",
        "inputSchema": GetNoticeInput.model_json_schema()
    },
    {
        "name": "get_filed_returns",
        "description": "List all GST returns (GSTR-3B, GSTR-2B, GSTR-1) filed for a specific GSTIN and tax period.",
        "inputSchema": GetFiledReturnsInput.model_json_schema()
    },
    {
        "name": "get_return_details",
        "description": "Fetch line-item details of a specific GST return (e.g., invoices inside GSTR-2B).",
        "inputSchema": GetReturnDetailsInput.model_json_schema()
    },
    {
        "name": "get_vendor_filing_status",
        "description": "Check whether a supplier has filed GSTR-1 and GSTR-3B for a given tax period.",
        "inputSchema": GetVendorFilingStatusInput.model_json_schema()
    }
]

# Business Logic Implementations
def execute_get_notice(args: Dict[str, Any]) -> Dict[str, Any]:
    notice_id = args.get("notice_id", "").strip()
    notice = MOCK_NOTICES.get(notice_id)
    if not notice:
        # Search by number suffix
        for k, v in MOCK_NOTICES.items():
            if notice_id in k:
                notice = v
                break
    if not notice:
        raise HTTPException(status_code=404, detail=f"Notice '{notice_id}' not found in portal database")
    res = dict(notice)
    res["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return res

def execute_get_filed_returns(args: Dict[str, Any]) -> Dict[str, Any]:
    gstin = args.get("gstin", "").strip()
    tax_period = args.get("tax_period", "").strip()
    key = (gstin, tax_period)
    returns = MOCK_FILED_RETURNS.get(key, [])
    return {
        "source_id": f"SRC-RETURNS-{gstin}-{tax_period}",
        "gstin": gstin,
        "tax_period": tax_period,
        "returns": returns,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

def execute_get_return_details(args: Dict[str, Any]) -> Dict[str, Any]:
    gstin = args.get("gstin", "").strip()
    return_type = args.get("return_type", "").strip()
    tax_period = args.get("tax_period", "").strip()
    key = (gstin, return_type, tax_period)
    line_items = MOCK_RETURN_DETAILS.get(key, [])
    return {
        "source_id": f"SRC-DETAILS-{gstin}-{return_type}-{tax_period}",
        "gstin": gstin,
        "return_type": return_type,
        "tax_period": tax_period,
        "line_items": line_items,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

def execute_get_vendor_filing_status(args: Dict[str, Any]) -> Dict[str, Any]:
    supplier_gstin = args.get("supplier_gstin", "").strip()
    tax_period = args.get("tax_period", "").strip()
    key = (supplier_gstin, tax_period)
    status_record = MOCK_VENDOR_STATUS.get(key)
    if not status_record:
        return {
            "source_id": f"SRC-VEN-{supplier_gstin}-{tax_period}",
            "supplier_gstin": supplier_gstin,
            "supplier_name": "Unknown / Unregistered Supplier",
            "tax_period": tax_period,
            "gstr1_status": "NOT_FILED",
            "gstr1_filing_date": None,
            "gstr1_arn": None,
            "gstr3b_status": "NOT_FILED",
            "gstr3b_filing_date": None,
            "invoices_reported": 0,
            "total_invoice_value": 0.0,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
    res = dict(status_record)
    res["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return res

# Standard MCP JSON-RPC 2.0 Handler
@app.post("/mcp")
async def mcp_rpc(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})

    method = body.get("method")
    rpc_id = body.get("id")
    params = body.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "tax-portal-mcp", "version": "1.0.0"}
            },
            "id": rpc_id
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {"tools": TAX_PORTAL_TOOLS},
            "id": rpc_id
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            if tool_name == "get_notice":
                result_data = execute_get_notice(arguments)
            elif tool_name == "get_filed_returns":
                result_data = execute_get_filed_returns(arguments)
            elif tool_name == "get_return_details":
                result_data = execute_get_return_details(arguments)
            elif tool_name == "get_vendor_filing_status":
                result_data = execute_get_vendor_filing_status(arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},
                    "id": rpc_id
                }

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result_data)}],
                    "isError": False
                },
                "id": rpc_id
            }
        except HTTPException as e:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": e.detail})}],
                    "isError": True
                },
                "id": rpc_id
            }
        except Exception as ex:
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(ex)})}],
                    "isError": True
                },
                "id": rpc_id
            }

    return {
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": f"Unknown method '{method}'"},
        "id": rpc_id
    }

# Health & direct REST tool calls for testing
@app.get("/health")
def health():
    return {"status": "healthy", "server": "Tax Portal MCP Server", "port": 8001}

@app.get("/tools")
def list_tools():
    return {"tools": TAX_PORTAL_TOOLS}

if __name__ == "__main__":
    uvicorn.run("app.mcp.servers.tax_portal_server:app", host="0.0.0.0", port=8001, reload=False)
