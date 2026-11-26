import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from app.mcp.contracts.schemas import (
    GetEntriesByPeriodInput, GetEntriesByPeriodOutput,
    GetInvoiceDetailsInput, InvoiceDetailOutput,
    SearchInvoicesInput, SearchInvoicesOutput,
    GetLedgerRecordsInput, GetLedgerRecordsOutput
)

app = FastAPI(
    title="Ledger MCP Server",
    description="Simulated Accounting Ledger MCP Server for TaxPilot AI",
    version="1.0.0"
)

# Realistic Synthetic Accounting Ledger Mock Dataset
MOCK_INVOICES = {
    "INV-2023-0891": {
        "source_id": "SRC-INV-0891",
        "invoice_number": "INV-2023-0891",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "buyer_gstin": "27AABCT1234C1Z5",
        "invoice_date": "2023-11-28",
        "tax_period": "2023-11",
        "taxable_amount": 450000.0,
        "cgst_amount": 40500.0,
        "sgst_amount": 40500.0,
        "igst_amount": 0.0,
        "total_tax": 81000.0,
        "invoice_value": 531000.0,
        "payment_status": "PAID",
        "po_number": "PO-2023-1104",
        "e_way_bill_no": "241098234511"
    },
    "DL-8841": {
        "source_id": "SRC-INV-DL8841",
        "invoice_number": "DL-8841",
        "supplier_gstin": "07AAACD7777E1Z3",
        "supplier_name": "Delta Electricals India Ltd",
        "buyer_gstin": "27AABCT1234C1Z5",
        "invoice_date": "2023-11-15",
        "tax_period": "2023-11",
        "taxable_amount": 320000.0,
        "cgst_amount": 0.0,
        "sgst_amount": 0.0,
        "igst_amount": 57600.0,
        "total_tax": 57600.0,
        "invoice_value": 377600.0,
        "payment_status": "PAID",
        "po_number": "PO-2023-0982",
        "e_way_bill_no": "119823459012"
    },
    "SP-5501": {
        "source_id": "SRC-INV-SP5501",
        "invoice_number": "SP-5501",
        "supplier_gstin": "27AAACS1111B1Z2",
        "supplier_name": "Surya Packaging Industries",
        "buyer_gstin": "27AABCT1234C1Z5",
        "invoice_date": "2023-10-31",
        "tax_period": "2023-10",
        "taxable_amount": 200000.0,
        "cgst_amount": 18000.0,
        "sgst_amount": 18000.0,
        "igst_amount": 0.0,
        "total_tax": 36000.0,
        "invoice_value": 236000.0,
        "payment_status": "PAID",
        "po_number": "PO-2023-0871",
        "e_way_bill_no": None
    },
    "INV-2026-0511": {
        "source_id": "SRC-INV-0511",
        "invoice_number": "INV-2026-0511",
        "supplier_gstin": "34XYZAB9876C1Z2",
        "supplier_name": "Coastal Hardware Supplies",
        "buyer_gstin": "34ABCDE1234F1Z5",
        "invoice_date": "2026-05-18",
        "tax_period": "2026-05",
        "taxable_amount": 8000.0,
        "cgst_amount": 720.0,
        "sgst_amount": 720.0,
        "igst_amount": 0.0,
        "total_tax": 1440.0,
        "invoice_value": 9440.0,
        "payment_status": "PAID",
        "po_number": "PO-2026-0512",
        "e_way_bill_no": "341098234511"
    },
    "INV-2023-9941": {
        "source_id": "SRC-INV-9941",
        "invoice_number": "INV-2023-9941",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "buyer_gstin": "33AABCA1234F1Z5",
        "invoice_date": "2023-11-20",
        "tax_period": "2023-11",
        "taxable_amount": 777777.78,
        "cgst_amount": 35000.0,
        "sgst_amount": 35000.0,
        "igst_amount": 70000.0,
        "total_tax": 140000.0,
        "invoice_value": 917777.78,
        "payment_status": "PAID",
        "po_number": "PO-2023-9901",
        "e_way_bill_no": "331098234588"
    },
    "INV-2026-0184": {
        "source_id": "SRC-INV-0184",
        "invoice_number": "INV-2026-0184",
        "supplier_gstin": "27AABCS5555D1Z8",
        "supplier_name": "Apex Logistics Services Pvt Ltd",
        "buyer_gstin": "33AABCA1234F1Z5",
        "invoice_date": "2026-11-10",
        "tax_period": "2026-11",
        "taxable_amount": 777777.78,
        "cgst_amount": 35000.0,
        "sgst_amount": 35000.0,
        "igst_amount": 70000.0,
        "total_tax": 140000.0,
        "invoice_value": 917777.78,
        "payment_status": "PAID",
        "po_number": "PO-2026-0184",
        "e_way_bill_no": "331098234599"
    }
}

MOCK_LEDGER_ENTRIES = [
    {
        "source_id": "LED-202605-001",
        "entry_date": "2026-05-20",
        "tax_period": "2026-05",
        "account_code": "ITC-CGST-INPUT",
        "account_name": "Input CGST Receivable",
        "narration": "Input credit booked on Coastal Hardware INV-2026-0511",
        "debit_amount": 720.0,
        "credit_amount": 0.0,
        "gstin": "34ABCDE1234F1Z5",
        "invoice_reference": "INV-2026-0511"
    },
    {
        "source_id": "LED-202605-002",
        "entry_date": "2026-05-20",
        "tax_period": "2026-05",
        "account_code": "ITC-SGST-INPUT",
        "account_name": "Input SGST Receivable",
        "narration": "Input credit booked on Coastal Hardware INV-2026-0511",
        "debit_amount": 720.0,
        "credit_amount": 0.0,
        "gstin": "34ABCDE1234F1Z5",
        "invoice_reference": "INV-2026-0511"
    },
    {
        "source_id": "LED-202311-001",
        "entry_date": "2023-11-28",
        "tax_period": "2023-11",
        "account_code": "ITC-CGST-INPUT",
        "account_name": "Input CGST Receivable",
        "narration": "Input credit booked for logistics on INV-2023-0891",
        "debit_amount": 40500.0,
        "credit_amount": 0.0,
        "gstin": "27AABCT1234C1Z5",
        "invoice_reference": "INV-2023-0891"
    },
    {
        "source_id": "LED-202311-002",
        "entry_date": "2023-11-28",
        "tax_period": "2023-11",
        "account_code": "ITC-SGST-INPUT",
        "account_name": "Input SGST Receivable",
        "narration": "Input credit booked for logistics on INV-2023-0891",
        "debit_amount": 40500.0,
        "credit_amount": 0.0,
        "gstin": "27AABCT1234C1Z5",
        "invoice_reference": "INV-2023-0891"
    },
    {
        "source_id": "LED-202311-003",
        "entry_date": "2023-11-15",
        "tax_period": "2023-11",
        "account_code": "ITC-IGST-INPUT",
        "account_name": "Input IGST Receivable",
        "narration": "Input credit for electrical supplies on DL-8841",
        "debit_amount": 57600.0,
        "credit_amount": 0.0,
        "gstin": "27AABCT1234C1Z5",
        "invoice_reference": "DL-8841"
    },
    {
        "source_id": "LED-202611-001",
        "entry_date": "2026-11-20",
        "tax_period": "2026-11",
        "account_code": "ITC-IGST-INPUT",
        "account_name": "Input IGST Receivable",
        "narration": "Input credit for logistics on INV-2026-0184",
        "debit_amount": 70000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2026-0184"
    },
    {
        "source_id": "LED-202611-002",
        "entry_date": "2026-11-20",
        "tax_period": "2026-11",
        "account_code": "ITC-CGST-INPUT",
        "account_name": "Input CGST Receivable",
        "narration": "Input credit for logistics on INV-2026-0184",
        "debit_amount": 35000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2026-0184"
    },
    {
        "source_id": "LED-202611-003",
        "entry_date": "2026-11-20",
        "tax_period": "2026-11",
        "account_code": "ITC-SGST-INPUT",
        "account_name": "Input SGST Receivable",
        "narration": "Input credit for logistics on INV-2026-0184",
        "debit_amount": 35000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2026-0184"
    },
    {
        "source_id": "LED-202311-004",
        "entry_date": "2023-11-20",
        "tax_period": "2023-11",
        "account_code": "ITC-IGST-INPUT",
        "account_name": "Input IGST Receivable",
        "narration": "Input credit for logistics on INV-2023-9941",
        "debit_amount": 70000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2023-9941"
    },
    {
        "source_id": "LED-202311-005",
        "entry_date": "2023-11-20",
        "tax_period": "2023-11",
        "account_code": "ITC-CGST-INPUT",
        "account_name": "Input CGST Receivable",
        "narration": "Input credit for logistics on INV-2023-9941",
        "debit_amount": 35000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2023-9941"
    },
    {
        "source_id": "LED-202311-006",
        "entry_date": "2023-11-20",
        "tax_period": "2023-11",
        "account_code": "ITC-SGST-INPUT",
        "account_name": "Input SGST Receivable",
        "narration": "Input credit for logistics on INV-2023-9941",
        "debit_amount": 35000.0,
        "credit_amount": 0.0,
        "gstin": "33AABCA1234F1Z5",
        "invoice_reference": "INV-2023-9941"
    }
]

# MCP Tools Registry definition
LEDGER_TOOLS = [
    {
        "name": "get_entries_by_period",
        "description": "Fetch journal entries and ledger movements for a GSTIN between a start date and an end date.",
        "inputSchema": GetEntriesByPeriodInput.model_json_schema()
    },
    {
        "name": "get_invoice_details",
        "description": "Retrieve comprehensive invoice details (taxable value, CGST, SGST, IGST, E-way bill, payment status) by invoice ID.",
        "inputSchema": GetInvoiceDetailsInput.model_json_schema()
    },
    {
        "name": "search_invoices",
        "description": "Search purchase invoices by supplier GSTIN, tax period, and amount with tolerance matching.",
        "inputSchema": SearchInvoicesInput.model_json_schema()
    },
    {
        "name": "get_ledger_records",
        "description": "Fetch ledger transactions associated with a specific invoice number to verify accounting reconciliation.",
        "inputSchema": GetLedgerRecordsInput.model_json_schema()
    }
]

def execute_get_entries_by_period(args: Dict[str, Any]) -> Dict[str, Any]:
    gstin = args.get("gstin", "").strip()
    start_date = args.get("start_date", "").strip()
    end_date = args.get("end_date", "").strip()
    
    matched_entries = []
    total_debits = 0.0
    total_credits = 0.0
    for e in MOCK_LEDGER_ENTRIES:
        if e["gstin"] == gstin:
            if (not start_date or e["entry_date"] >= start_date) and (not end_date or e["entry_date"] <= end_date):
                matched_entries.append(e)
                total_debits += e["debit_amount"]
                total_credits += e["credit_amount"]

    return {
        "source_id": f"SRC-LED-PERIOD-{gstin}-{start_date}-{end_date}",
        "gstin": gstin,
        "start_date": start_date,
        "end_date": end_date,
        "total_debits": total_debits,
        "total_credits": total_credits,
        "entries": matched_entries,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

def execute_get_invoice_details(args: Dict[str, Any]) -> Dict[str, Any]:
    invoice_id = args.get("invoice_id", "").strip()
    inv = MOCK_INVOICES.get(invoice_id)
    if not inv:
        # Try search by partial match
        for k, v in MOCK_INVOICES.items():
            if invoice_id in k or k in invoice_id:
                inv = v
                break
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found in accounting ledger")
    res = dict(inv)
    res["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return res

def execute_search_invoices(args: Dict[str, Any]) -> Dict[str, Any]:
    supplier_gstin = args.get("supplier_gstin")
    tax_period = args.get("tax_period")
    amount = args.get("amount")
    tolerance = args.get("amount_tolerance", 100.0)

    matches = []
    for inv in MOCK_INVOICES.values():
        match = True
        if supplier_gstin and inv["supplier_gstin"] != supplier_gstin:
            match = False
        if tax_period and inv["tax_period"] != tax_period:
            match = False
        if amount is not None:
            # Check total tax or invoice value within tolerance
            diff_tax = abs(inv["total_tax"] - float(amount))
            diff_val = abs(inv["invoice_value"] - float(amount))
            if diff_tax > tolerance and diff_val > tolerance:
                match = False
        if match:
            res_inv = dict(inv)
            res_inv["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            matches.append(res_inv)

    # Fallback search if exact period+amount matched 0
    if not matches and amount is not None:
        for inv in MOCK_INVOICES.values():
            diff_tax = abs(inv["total_tax"] - float(amount))
            diff_val = abs(inv["invoice_value"] - float(amount))
            if diff_tax <= max(tolerance, 1000.0) or diff_val <= max(tolerance, 1000.0):
                res_inv = dict(inv)
                res_inv["retrieved_at"] = datetime.now(timezone.utc).isoformat()
                matches.append(res_inv)

    return {
        "source_id": f"SRC-INV-SEARCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "query_params": args,
        "total_matches": len(matches),
        "matches": matches,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

def execute_get_ledger_records(args: Dict[str, Any]) -> Dict[str, Any]:
    invoice_id = args.get("invoice_id", "").strip()
    matched = [e for e in MOCK_LEDGER_ENTRIES if e.get("invoice_reference") == invoice_id]
    total_claimed = sum(e["debit_amount"] for e in matched)
    reconciliation_status = "RECONCILED" if len(matched) > 0 else "UNMATCHED"

    return {
        "source_id": f"SRC-LED-REC-{invoice_id}",
        "invoice_id": invoice_id,
        "reconciliation_status": reconciliation_status,
        "entries": matched,
        "total_claimed_in_ledger": total_claimed,
        "retrieved_at": datetime.now(timezone.utc).isoformat()
    }

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
                "serverInfo": {"name": "ledger-mcp", "version": "1.0.0"}
            },
            "id": rpc_id
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {"tools": LEDGER_TOOLS},
            "id": rpc_id
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            if tool_name == "get_entries_by_period":
                result_data = execute_get_entries_by_period(arguments)
            elif tool_name == "get_invoice_details":
                result_data = execute_get_invoice_details(arguments)
            elif tool_name == "search_invoices":
                result_data = execute_search_invoices(arguments)
            elif tool_name == "get_ledger_records":
                result_data = execute_get_ledger_records(arguments)
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

@app.get("/health")
def health():
    return {"status": "healthy", "server": "Ledger MCP Server", "port": 8002}

@app.get("/tools")
def list_tools():
    return {"tools": LEDGER_TOOLS}

if __name__ == "__main__":
    uvicorn.run("app.mcp.servers.ledger_server:app", host="0.0.0.0", port=8002, reload=False)
