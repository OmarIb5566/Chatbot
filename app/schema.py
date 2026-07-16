"""Whitelisted schema for the SQL agent.

Only these 3 tables/columns may ever be touched by generated SQL. Column
names are stored with their real, case-sensitive spelling because Postgres
created these tables with quoted (mixed-case) identifiers - referencing them
unquoted or with the wrong case will fail to resolve.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnDef:
    name: str  # exact, case-sensitive Postgres column name
    type: str  # human-readable type, for the LLM prompt


@dataclass(frozen=True)
class TableDef:
    name: str  # lowercase physical table name
    join_column: str  # exact column name used to join to dim_projects
    columns: tuple[ColumnDef, ...]
    description: str


DIM_PROJECTS = TableDef(
    name="dim_projects",
    join_column="PROJECT_ID",
    description="The master project dimension. Every other table joins back to this one via PROJECT_ID.",
    columns=(
        ColumnDef("PROJECT_ID", "bigint, primary key"),
        ColumnDef("PROJECT_CODE", "varchar, unique project code"),
        ColumnDef(
            "NAME",
            "varchar, the canonical/master project name - prefer this table+column for any general "
            "'project name' lookup unless the question is specifically about how the name was recorded "
            "on a particular payment or PO line",
        ),
        ColumnDef("PROJECT_OWNER", "varchar"),
        ColumnDef("BUSINESS_UNIT", "varchar"),
        ColumnDef("ORG_ID", "bigint"),
        ColumnDef("PROJECT_SECTOR_MANAGER", "varchar"),
        ColumnDef("SECONDARY_INVENTORY_NAME", "varchar"),
        ColumnDef("ORGANIZATION_ID", "bigint"),
        ColumnDef("COUNTRY_NAME", "varchar"),
        ColumnDef("EMAIL_ADDRESS", "varchar"),
        ColumnDef("SOURCE", "varchar"),
    ),
)

FACT_AP_CHECK_PAYMENTS = TableDef(
    name="fact_ap_check_payments",
    join_column="PROJECT_ID",
    description="AP (accounts payable) check payment facts - one row per payment/check line.",
    columns=(
        ColumnDef("PROJECT_ID", "bigint, FK to dim_projects.PROJECT_ID"),
        ColumnDef("Document_Number", "varchar, invoice document number"),
        ColumnDef("INVOICE_NUM", "varchar, invoice number"),
        ColumnDef("INVOICE_ID", "bigint, invoice identifier"),
        ColumnDef("COMP_ID", "bigint, company identifier"),
        ColumnDef(
            "PAYMENT_AMOUNT",
            "numeric, the invoice/payment amount in its original currency - pair with \"Currency\" when "
            "reporting it. This is usually what 'invoice amount' / 'outstanding invoice' refers to.",
        ),
        ColumnDef(
            "EQUIV",
            "numeric, PAYMENT_AMOUNT converted to Egyptian pounds (EGP) only - use when the question "
            "wants EGP regardless of the original currency",
        ),
        ColumnDef(
            "PROJECT_NUMBER",
            'varchar, DUPLICATE of "PROJECT_CODE" - do not use, use "PROJECT_CODE" instead',
        ),
        ColumnDef("PROJECT", "varchar, project name as recorded on the payment"),
        ColumnDef("OWNER", "varchar, project owner as recorded on the payment"),
        ColumnDef("SECTOR", "varchar"),
        ColumnDef("Supplier_Number", "varchar"),
        ColumnDef("Supplier_Name", "varchar"),
        ColumnDef("CHECK_ID", "bigint"),
        ColumnDef("CE_BANK_ACCT_USE_ID", "bigint"),
        ColumnDef("BANK_ACCOUNT_ID", "bigint"),
        ColumnDef("VENDOR_ID", "bigint"),
        ColumnDef("PAYCARD_AUTHORIZATION_NUMBER", "varchar"),
        ColumnDef("BANK_ACCOUNT_NAME", "varchar"),
        ColumnDef(
            "Payment_Reconcilation_Status",
            "varchar, status of the invoice/payment. Only valid values: 'CLEARED', "
            "'CLEARED BUT UNACCOUNTED', 'ISSUED', 'NEGOTIABLE', 'RECONCILED', 'RECONCILED UNACCOUNTED', "
            "'VOIDED' - note none of these literally contain the word 'outstanding', so never filter with "
            "ILIKE '%outstanding%'. An invoice is outstanding when Payment_Reconcilation_Status is "
            "'ISSUED', 'NEGOTIABLE', or 'VOIDED', OR when (PAYMENT_AMOUNT or EQUIV) - Cleared_Amount > 0.",
        ),
        ColumnDef(
            "Cleared_Amount",
            "numeric, the amount that has actually been paid/cleared so far - compare against "
            "PAYMENT_AMOUNT/EQUIV to gauge how much of an invoice is still outstanding",
        ),
        ColumnDef("Currency", "varchar, currency code that PAYMENT_AMOUNT is denominated in"),
        ColumnDef("Cleared_Date", "timestamp, date the payment was cleared"),
        ColumnDef("CHECK_DATE", "timestamp, date the check was issued"),
        ColumnDef(
            "MATURATY_DATE",
            "timestamp, invoice due/maturity date - relevant for 'outstanding'/overdue questions",
        ),
        ColumnDef(
            "STATUS_LOOKUP_CODE",
            "varchar, additional payment status code, alongside Payment_Reconcilation_Status",
        ),
        ColumnDef("VENDOR_SITE_CODE", "varchar"),
        ColumnDef("ORG_NAME", "varchar, organization name"),
        ColumnDef("ORG_ID", "bigint, organization identifier"),
        ColumnDef(
            "AMOUNT",
            'numeric, DUPLICATE of "Cleared_Amount" - do not use, use "Cleared_Amount" instead',
        ),
        ColumnDef("ATTRIBUTE7", "always NULL in this table - do not use"),
        ColumnDef("COST_CENTER", "always NULL in this table - do not use"),
        ColumnDef("CATEGORY", "always NULL in this table - do not use"),
        ColumnDef("PROJECT_CODE", "varchar"),
    ),
)

FACT_PO_FOLLOWUP = TableDef(
    name="fact_po_followup",
    join_column="project_id",
    description="Purchase-order followup facts - one row per PO line, with sourcing/receiving/invoicing progress.",
    columns=(
        ColumnDef("recovery_tax", "double precision"),
        ColumnDef("tax_code", "text"),
        ColumnDef("converted_tax", "double precision"),
        ColumnDef("po_header_id", "bigint"),
        ColumnDef("po_line_id", "bigint"),
        ColumnDef("exp_type", "text"),
        ColumnDef("exp_category", "text"),
        ColumnDef("tsk", "text, short for 'task' - task code, pair with tsk_name/task_id"),
        ColumnDef("task_id", "double precision, task identifier, pair with tsk/tsk_name"),
        ColumnDef("attribute4", "text"),
        ColumnDef("tsk_name", "text, task name, pair with tsk/task_id"),
        ColumnDef("line_location_id", "bigint"),
        ColumnDef("po_distribution_id", "bigint"),
        ColumnDef("po_num", "text"),
        ColumnDef("po_num_line", "text"),
        ColumnDef("comments", "text"),
        ColumnDef("comments_line", "text"),
        ColumnDef("term", "text"),
        ColumnDef("term_desc", "text"),
        ColumnDef("curr_line", "text"),
        ColumnDef("poh_creation_date", "timestamp"),
        ColumnDef("poh_crt_dt_line", "timestamp"),
        ColumnDef("approved_date", "timestamp"),
        ColumnDef("aprv_date_line", "timestamp"),
        ColumnDef("line_num", "bigint"),
        ColumnDef("unit_meas_lookup_code", "text"),
        ColumnDef("item_description", "text"),
        ColumnDef("unit_price", "double precision"),
        ColumnDef("unit_price_with_tax", "double precision"),
        ColumnDef("req_dept", "text"),
        ColumnDef("need_by_date", "timestamp"),
        ColumnDef("quantity_ordered", "double precision"),
        ColumnDef("quantity_billed", "double precision"),
        ColumnDef("quantity_delivered", "double precision"),
        ColumnDef("quantity_cancelled", "double precision"),
        ColumnDef("quantity_received", "double precision"),
        ColumnDef("quantity_accepted", "double precision"),
        ColumnDef("quantity_rejected", "bigint"),
        ColumnDef("currency_code", "text"),
        ColumnDef("line_amount", "double precision"),
        ColumnDef("line_amount_without_tax", "double precision"),
        ColumnDef("open_qty_unit_price", "double precision"),
        ColumnDef("open_qty_amount", "double precision"),
        ColumnDef("converted_line_amount", "double precision"),
        ColumnDef("converted_amount_without_tax", "double precision"),
        ColumnDef("current_rate", "double precision"),
        ColumnDef("open", "double precision"),
        ColumnDef("project_num", "text"),
        ColumnDef("project_name", "text"),
        ColumnDef("organization_code", "text"),
        ColumnDef("item_code", "text"),
        ColumnDef("pr_num", "text"),
        ColumnDef("pr_num2", "text"),
        ColumnDef("pr_line_num", "double precision"),
        ColumnDef("vendor_name", "text, supplier/vendor name, pair with vendor_no"),
        ColumnDef("vendor_no", "varchar, supplier/vendor number, pair with vendor_name"),
        ColumnDef("vendor_name_line", 'text, DUPLICATE of "vendor_name" - do not use'),
        ColumnDef(
            "buyer_name",
            "text, the person within the company who made the purchase - pair with buyer_dep",
        ),
        ColumnDef("buyer_name_line", 'text, DUPLICATE of "buyer_name" - do not use'),
        ColumnDef("pr_category", "text"),
        ColumnDef("pr_reason", "text"),
        ColumnDef("authorization_status", "text"),
        ColumnDef("promised_date", "timestamp"),
        ColumnDef("delv", "text"),
        ColumnDef("shipment_cancel_status", "text"),
        ColumnDef("shipment_close_status", "text"),
        ColumnDef("buyer_dep", "text"),
        ColumnDef("quantity open amount", "double precision, NOTE: column name contains spaces, must always be double-quoted"),
        ColumnDef("item_id", "varchar"),
        ColumnDef("project_id", "bigint, FK to dim_projects.PROJECT_ID"),
    ),
)

TABLES: dict[str, TableDef] = {
    t.name: t
    for t in (DIM_PROJECTS, FACT_AP_CHECK_PAYMENTS, FACT_PO_FOLLOWUP)
}

# lowercase column name -> exact column name, per table (used by the validator
# to resolve whatever case the LLM emits back to the real Postgres identifier)
TABLE_COLUMN_LOOKUP: dict[str, dict[str, str]] = {
    table.name: {col.name.lower(): col.name for col in table.columns}
    for table in TABLES.values()
}


def render_schema_for_prompt() -> str:
    lines = [
        "You may ONLY query these 3 PostgreSQL tables (schema `public`). "
        "All are linked through the project dimension `dim_projects`:",
        "",
    ]
    for table in TABLES.values():
        lines.append(f"TABLE {table.name} -- {table.description}")
        lines.append(f"  join key: \"{table.join_column}\" -> dim_projects.\"PROJECT_ID\"")
        for col in table.columns:
            lines.append(f'  - "{col.name}" ({col.type})')
        lines.append("")
    lines.append(
        "Join rule: dim_projects.\"PROJECT_ID\" = fact_ap_check_payments.\"PROJECT_ID\" "
        "= fact_po_followup.project_id"
    )
    lines.append(
        "Every column name above must be written EXACTLY as shown, double-quoted, "
        "preserving upper/lower case (Postgres identifiers are case-sensitive here)."
    )
    lines.append("")
    lines.append(
        "Business term glossary (use this to resolve ambiguous business language to the right column):"
    )
    lines.append(
        '- "project name": prefer dim_projects."NAME" (canonical). Only use '
        'fact_ap_check_payments."PROJECT" or fact_po_followup.project_name if the question is '
        "specifically about the name as recorded on a payment or PO line, not a general project lookup."
    )
    lines.append(
        '- "invoice amount": fact_ap_check_payments."PAYMENT_AMOUNT" (paired with "Currency") or '
        '"EQUIV" (EGP only).'
    )
    lines.append(
        '- "outstanding invoice" on fact_ap_check_payments: an invoice is outstanding when '
        '"Payment_Reconcilation_Status" IN (\'ISSUED\', \'NEGOTIABLE\', \'VOIDED\'), OR when '
        '("PAYMENT_AMOUNT" or "EQUIV") - "Cleared_Amount" > 0. The outstanding amount itself is '
        '("PAYMENT_AMOUNT" or "EQUIV") - "Cleared_Amount". Never match "Payment_Reconcilation_Status" '
        "with ILIKE '%outstanding%' or '=' 'OUTSTANDING' - that value never appears in the data; its "
        "only valid values are 'CLEARED', 'CLEARED BUT UNACCOUNTED', 'ISSUED', 'NEGOTIABLE', "
        "'RECONCILED', 'RECONCILED UNACCOUNTED', 'VOIDED'."
    )
    lines.append(
        '- "supplier"/"vendor" on payments: fact_ap_check_payments."Supplier_Name"/"Supplier_Number". '
        "On purchase orders: fact_po_followup.vendor_name/vendor_no."
    )
    lines.append(
        '- "buyer"/"purchaser": fact_po_followup.buyer_name, paired with buyer_dep (the buyer\'s department).'
    )
    lines.append('- "task": fact_po_followup.tsk / tsk_name / task_id.')
    lines.append(
        '- Never use a column annotated "do not use" above - use the column it references instead.'
    )
    return "\n".join(lines)
