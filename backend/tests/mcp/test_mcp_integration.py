import pytest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, backend_dir)

from app.mcp.client.manager import mcp_client

@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    await mcp_client.initialize()
    tools = mcp_client.list_tools()
    tool_names = [t["name"] for t in tools]

    # Verify all 4 tools from Tax Portal Server
    assert "get_notice" in tool_names
    assert "get_filed_returns" in tool_names
    assert "get_return_details" in tool_names
    assert "get_vendor_filing_status" in tool_names

    # Verify all 4 tools from Ledger Server
    assert "get_entries_by_period" in tool_names
    assert "get_invoice_details" in tool_names
    assert "search_invoices" in tool_names
    assert "get_ledger_records" in tool_names

@pytest.mark.asyncio
async def test_mcp_get_notice():
    await mcp_client.initialize()
    notice_data = await mcp_client.invoke_tool("get_notice", {"notice_id": "ZA271223001928K"})
    assert notice_data["notice_number"] == "ZA271223001928K"
    assert notice_data["itc_mismatch"] == 81000.0
    assert notice_data["gstin"] == "27AABCT1234C1Z5"
    assert "source_id" in notice_data

@pytest.mark.asyncio
async def test_mcp_get_vendor_filing_status_timing_difference():
    await mcp_client.initialize()
    # In Nov 2023, supplier had NOT filed GSTR-1
    res_nov = await mcp_client.invoke_tool(
        "get_vendor_filing_status",
        {"supplier_gstin": "27AABCS5555D1Z8", "tax_period": "2023-11"}
    )
    assert res_nov["gstr1_status"] == "NOT_FILED"

    # In Dec 2023, supplier filed GSTR-1 on 11-Jan-2024
    res_dec = await mcp_client.invoke_tool(
        "get_vendor_filing_status",
        {"supplier_gstin": "27AABCS5555D1Z8", "tax_period": "2023-12"}
    )
    assert res_dec["gstr1_status"] == "FILED"
    assert res_dec["gstr1_filing_date"] == "2024-01-11"
    assert res_dec["total_invoice_value"] == 531000.0

@pytest.mark.asyncio
async def test_mcp_ledger_get_invoice_details():
    await mcp_client.initialize()
    inv_data = await mcp_client.invoke_tool("get_invoice_details", {"invoice_id": "INV-2023-0891"})
    assert inv_data["invoice_number"] == "INV-2023-0891"
    assert inv_data["supplier_gstin"] == "27AABCS5555D1Z8"
    assert inv_data["total_tax"] == 81000.0
    assert inv_data["payment_status"] == "PAID"
    assert "source_id" in inv_data

@pytest.mark.asyncio
async def test_mcp_search_invoices():
    await mcp_client.initialize()
    res = await mcp_client.invoke_tool("search_invoices", {
        "supplier_gstin": "27AABCS5555D1Z8",
        "tax_period": "2023-11",
        "amount": 81000.0
    })
    assert res["total_matches"] == 1
    assert res["matches"][0]["invoice_number"] == "INV-2023-0891"

@pytest.mark.asyncio
async def test_mcp_unknown_tool_error():
    await mcp_client.initialize()
    with pytest.raises(ValueError, match="not registered"):
        await mcp_client.invoke_tool("non_existent_tool", {})
