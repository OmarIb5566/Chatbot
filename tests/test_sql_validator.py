import pytest

from app.sql_validator import SQLValidationError, validate_and_prepare


def test_allows_simple_select():
    sql = 'SELECT "PROJECT_ID", "NAME" FROM dim_projects LIMIT 10'
    out = validate_and_prepare(sql, max_rows=200)
    assert "dim_projects" in out
    assert "LIMIT 10" in out


def test_injects_limit_when_missing():
    sql = 'SELECT "PROJECT_ID" FROM dim_projects'
    out = validate_and_prepare(sql, max_rows=50)
    assert "LIMIT 50" in out


def test_caps_limit_above_max():
    sql = 'SELECT "PROJECT_ID" FROM dim_projects LIMIT 100000'
    out = validate_and_prepare(sql, max_rows=50)
    assert "LIMIT 50" in out
    assert "100000" not in out


def test_allows_join_across_whitelisted_tables():
    sql = (
        'SELECT p."NAME", f."Cleared_Amount" '
        'FROM dim_projects p JOIN fact_ap_check_payments f '
        'ON p."PROJECT_ID" = f."PROJECT_ID" LIMIT 10'
    )
    out = validate_and_prepare(sql, max_rows=200)
    assert "fact_ap_check_payments" in out


def test_allows_cte():
    sql = (
        "WITH totals AS (SELECT project_id, SUM(line_amount) AS total "
        "FROM fact_po_followup GROUP BY project_id) "
        "SELECT * FROM totals LIMIT 10"
    )
    out = validate_and_prepare(sql, max_rows=200)
    assert "totals" in out


def test_rejects_non_whitelisted_table():
    sql = 'SELECT * FROM dim_clients LIMIT 10'
    with pytest.raises(SQLValidationError, match="not one of the allowed tables"):
        validate_and_prepare(sql, max_rows=200)


def test_rejects_non_whitelisted_table_in_join():
    sql = (
        'SELECT * FROM dim_projects p JOIN pg_roles r ON true LIMIT 10'
    )
    with pytest.raises(SQLValidationError):
        validate_and_prepare(sql, max_rows=200)


@pytest.mark.parametrize(
    "sql",
    [
        'DELETE FROM dim_projects WHERE "PROJECT_ID" = 1',
        'UPDATE dim_projects SET "NAME" = \'x\'',
        'DROP TABLE dim_projects',
        'INSERT INTO dim_projects ("PROJECT_ID") VALUES (1)',
        'TRUNCATE dim_projects',
    ],
)
def test_rejects_dml_and_ddl(sql):
    with pytest.raises(SQLValidationError):
        validate_and_prepare(sql, max_rows=200)


def test_rejects_multiple_statements():
    sql = 'SELECT 1; DROP TABLE dim_projects;'
    with pytest.raises(SQLValidationError, match="single SQL statement"):
        validate_and_prepare(sql, max_rows=200)


def test_rejects_forbidden_function():
    sql = "SELECT pg_sleep(10)"
    with pytest.raises(SQLValidationError, match="not allowed"):
        validate_and_prepare(sql, max_rows=200)


def test_rejects_empty_sql():
    with pytest.raises(SQLValidationError):
        validate_and_prepare("   ", max_rows=200)


def test_forces_nulls_last_on_order_by_desc():
    sql = (
        'SELECT "vendor_name", SUM("line_amount") AS total FROM fact_po_followup '
        'GROUP BY "vendor_name" ORDER BY total DESC LIMIT 5'
    )
    out = validate_and_prepare(sql, max_rows=200)
    assert "NULLS LAST" in out.upper()


def test_ascending_order_stays_nulls_last_by_default():
    # NULLS LAST is already Postgres's default for ASC, so sqlglot omits the
    # keyword (it only prints when it differs from the dialect default) -
    # the important thing is it never flips to NULLS FIRST.
    sql = 'SELECT "PROJECT_ID" FROM dim_projects ORDER BY "PROJECT_ID" ASC LIMIT 5'
    out = validate_and_prepare(sql, max_rows=200)
    assert "NULLS FIRST" not in out.upper()
