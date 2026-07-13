"""Defense-in-depth validation for LLM-generated SQL.

The DB role the app connects with (`rowad_agent`) is already restricted to
SELECT on exactly the 3 whitelisted tables and runs in a read-only
transaction (see the local role grants). This module is a second,
independent layer: it re-parses the SQL and rejects anything that isn't a
single, simple, read-only SELECT/CTE touching only the whitelisted tables,
and caps the returned row count.
"""

import sqlglot
from sqlglot import exp

from app.schema import TABLES

FORBIDDEN_FUNCS = {
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_read_file",
    "pg_ls_dir",
    "dblink",
    "dblink_connect",
    "lo_import",
    "lo_export",
}


class SQLValidationError(Exception):
    """Generated SQL failed safety validation."""


def validate_and_prepare(sql: str, max_rows: int) -> str:
    sql = sql.strip().strip(";").strip()
    if not sql:
        raise SQLValidationError("Generated SQL was empty.")

    try:
        statements = [s for s in sqlglot.parse(sql, dialect="postgres") if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError(f"Could not parse SQL: {exc}") from exc

    if len(statements) != 1:
        raise SQLValidationError("Only a single SQL statement is allowed.")

    root = statements[0]

    if not isinstance(root, (exp.Select, exp.With, exp.Union)):
        raise SQLValidationError(
            f"Only SELECT statements are allowed, got: {type(root).__name__}"
        )

    # collect any CTE aliases so they aren't mistaken for real tables
    cte_names = {cte.alias_or_name.lower() for cte in root.find_all(exp.CTE)}

    for table in root.find_all(exp.Table):
        table_name = table.name.lower()
        if table_name in cte_names:
            continue
        if table_name not in TABLES:
            raise SQLValidationError(
                f"Table \"{table.name}\" is not one of the allowed tables: "
                f"{', '.join(TABLES)}"
            )
        schema_name = table.db.lower() if table.db else ""
        if schema_name and schema_name != "public":
            raise SQLValidationError(f"Schema \"{table.db}\" is not allowed.")

    for func in root.find_all(exp.Anonymous, exp.Func):
        func_name = (func.name or getattr(func, "sql_name", lambda: "")()).lower()
        if func_name in FORBIDDEN_FUNCS:
            raise SQLValidationError(f"Function \"{func_name}\" is not allowed.")

    for node in root.find_all(exp.Into, exp.Lock):
        raise SQLValidationError(f"\"{type(node).__name__}\" clauses are not allowed.")

    _cap_row_limit(root, max_rows)
    _default_nulls_last(root)
    _skip_header_row(root, cte_names)

    return root.sql(dialect="postgres")


def _default_nulls_last(root: exp.Expression) -> None:
    """Postgres defaults DESC ordering to NULLS FIRST, which makes rows with a
    NULL aggregate/amount look like the "top" result. sqlglot resolves
    nulls-ordering to an explicit bool at parse time (there's no way to tell
    "explicit in the SQL" from "dialect default" afterwards), so we
    unconditionally force NULLS LAST on every ORDER BY key - rows with no
    data should never outrank rows that do, in either direction.
    """
    for ordered in root.find_all(exp.Ordered):
        ordered.set("nulls_first", False)


def _skip_header_row(root: exp.Expression, cte_names: set[str]) -> None:
    """Row 1 of every whitelisted base table is a stray header row left over
    from the warehouse's ETL import (the real column names, shifted down to
    row 2) - replace every reference to a base table with a derived table
    that scans in physical order and discards that first row, so callers
    never see it.
    """
    for table in list(root.find_all(exp.Table)):
        table_name = table.name.lower()
        if table_name in cte_names or table_name not in TABLES:
            continue
        alias = table.alias_or_name
        bare_table = exp.Table(
            this=table.this.copy(),
            db=table.args.get("db").copy() if table.args.get("db") else None,
            catalog=table.args.get("catalog").copy() if table.args.get("catalog") else None,
        )
        skip_query = exp.select("*").from_(bare_table).order_by("ctid").offset(1)
        derived = exp.Subquery(this=skip_query, alias=exp.TableAlias(this=exp.to_identifier(alias)))
        table.replace(derived)


def _cap_row_limit(root: exp.Expression, max_rows: int) -> None:
    select = root if isinstance(root, exp.Select) else root.find(exp.Select)
    if select is None:
        return
    existing = select.args.get("limit")
    if existing is None:
        select.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
        return
    try:
        current_value = int(existing.expression.this)
    except (AttributeError, ValueError, TypeError):
        current_value = max_rows + 1
    if current_value > max_rows:
        select.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
