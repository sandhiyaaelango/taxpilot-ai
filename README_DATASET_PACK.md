# TaxPilot AI — Starter Dataset Pack

All transaction-level data and PDFs in this pack are **synthetic demo records**. They are not sourced from real taxpayers and must not be represented as official GST records.

## Contents
- `structured_data/`: 12 CSV datasets matching the project data model.
- `sample_documents/notices/`: synthetic DRC-01C-style demo notice.
- `sample_documents/invoices/`: synthetic invoice PDFs.
- `reference_sources/legal_reference_dataset.csv`: official/public reference links for legal and GST workflow context.

## Starter test case
- Fictional client: ABC Traders (Synthetic Demo Client)
- Period: April–June 2026
- Notice: NTC-2026-001
- May illustrative mismatch: INR 1,440
- Supplier SUP003 is marked NOT_FILED; invoice INV003 is in the purchase register but intentionally absent from the GSTR-2B sample.
- Purchase register contains a duplicate INV002 row for duplicate-detection testing.
- Supplier confirmation is deliberately missing, so the Evidence Challenge Engine should not claim that the supplier explanation is fully proven.

## Important implementation notes
1. Treat supplier filing status as mock data, not a live GST portal fact.
2. Verify every amount and source record in code. Do not trust `relationship_hint` as the final evidence verdict.
3. A missing document or failed MCP call means UNVERIFIED, not CONTRADICTED.
4. The legal reference CSV is a link index, not a legal opinion or a complete legal knowledge base.
5. Do not connect to GST portal accounts or submit responses automatically in this demo.
6. Synthetic GSTINs are placeholders and may fail real GSTIN validation; use a separate clearly-marked synthetic validation mode.

## Official source links
- GSTN GSTR-2B FAQ: https://tutorial.gst.gov.in/userguide/returns/FAQ_gstr2b.htm
- GSTN DRC-01C manual: https://tutorial.gst.gov.in/downloads/news/return_compliance_itc_mismatch_intimation_in_form_gst_drc_01c.pdf
- GSTN matching tool manual: https://tutorial.gst.gov.in/downloads/matchingtool.pdf
- GSTN GSTR-3B manual: https://tutorial.gst.gov.in/userguide/returns/Create_and_Submit_GSTR3B.htm
- data.gov.in aggregate GST collections: https://www.data.gov.in/resource/stateut-wise-details-gross-goods-and-service-tax-gst-collection-2020-21-2024-25
