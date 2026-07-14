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
        ColumnDef("NAME", "varchar, project name"),
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
        ColumnDef("Document_Number", "varchar"),
        ColumnDef("INVOICE_NUM", "varchar"),
        ColumnDef("COMP_ID", "varchar"),
        ColumnDef("ATTRIBUTE7", "varchar"),
        ColumnDef("COST_CENTER", "varchar"),
        ColumnDef("INVOICE_ID", "varchar"),
        ColumnDef("PAYMENT_AMOUNT", "numeric"),
        ColumnDef("EQUIV", "numeric, equivalent amount"),
        ColumnDef("PROJECT_NUMBER", "varchar"),
        ColumnDef("PROJECT", "varchar, project name as recorded on the payment"),
        ColumnDef("OWNER", "varchar"),
        ColumnDef("SECTOR", "varchar"),
        ColumnDef("Supplier_Number", "varchar"),
        ColumnDef("Supplier_Name", "varchar"),
        ColumnDef("CHECK_ID", "bigint"),
        ColumnDef("CE_BANK_ACCT_USE_ID", "varchar"),
        ColumnDef("BANK_ACCOUNT_ID", "varchar"),
        ColumnDef("VENDOR_ID", "bigint"),
        ColumnDef("PAYCARD_AUTHORIZATION_NUMBER", "varchar"),
        ColumnDef("BANK_ACCOUNT_NAME", "varchar"),
        ColumnDef("Payment_Reconcilation_Status", "varchar"),
        ColumnDef("Cleared_Amount", "numeric"),
        ColumnDef("Currency", "varchar"),
        ColumnDef("Cleared_Date", "timestamp"),
        ColumnDef("CHECK_DATE", "timestamp"),
        ColumnDef("AMOUNT", "numeric"),
        ColumnDef("VENDOR_SITE_CODE", "varchar"),
        ColumnDef("ORG_NAME", "varchar"),
        ColumnDef("ORG_ID", "bigint"),
        ColumnDef("STATUS_LOOKUP_CODE", "varchar"),
        ColumnDef("MATURATY_DATE", "timestamp"),
        ColumnDef("CATEGORY", "varchar"),
        ColumnDef("PROJECT_ID", "bigint, FK to dim_projects.PROJECT_ID"),
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
        ColumnDef("tsk", "text"),
        ColumnDef("task_id", "double precision"),
        ColumnDef("attribute4", "text"),
        ColumnDef("tsk_name", "text"),
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
        ColumnDef("vendor_name", "text"),
        ColumnDef("vendor_no", "varchar"),
        ColumnDef("vendor_name_line", "text"),
        ColumnDef("buyer_name", "text"),
        ColumnDef("buyer_name_line", "text"),
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
    return "\n".join(lines)
