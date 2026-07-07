import logging
import re
from dataclasses import dataclass, field

from app import db, llm
from app.config import settings
from app.schema import render_schema_for_prompt
from app.sql_validator import SQLValidationError, validate_and_prepare

logger = logging.getLogger(__name__)

_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)

_SYSTEM_PROMPT = f"""You are a PostgreSQL expert generating read-only SQL for \
Rowad Modern Engineering, a construction company, over its data warehouse.

{render_schema_for_prompt()}

Rules:
- Output ONLY a single PostgreSQL SELECT statement (optionally with a WITH clause). No prose, no explanation.
- Wrap the SQL in a single ```sql code block.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, or any statement that is not a SELECT.
- Use double quotes around every column identifier exactly as given above (case matters).
- Use single quotes for string literals.
- Use ILIKE with '%...%' for fuzzy/partial text matches on names unless the user gives an exact code/ID.
  This applies to EVERY name/description column (project name, supplier name, item description, etc.) -
  never use "=" for a name given in natural language, since the exact stored spelling may differ.
- When the question needs data from more than one table, JOIN through dim_projects using the join keys given above.
- Always include a LIMIT clause (<= {settings.sql_max_rows}) unless the question clearly asks for a single aggregate value.
- If the question is ambiguous, make the most reasonable assumption instead of asking for clarification.
- When ranking or sorting by a numeric aggregate (SUM/AVG/COUNT of a nullable column), add a HAVING or WHERE
  condition excluding NULL results (or use NULLS LAST) so rows with no data don't appear as top/bottom results.
- fact_ap_check_payments and fact_po_followup both have a many-to-many relationship with dim_projects
  (many rows per project in each). If a question needs figures from BOTH fact tables for the same
  project(s), first aggregate each fact table separately per project (e.g. with a CTE doing GROUP BY
  project id), then join the two aggregated results together - never join the two fact tables directly
  on project id, since that fans out into a Cartesian product and inflates sums/counts.
"""

_ARTICULATION_SYSTEM_PROMPT = """You are a helpful data analyst assistant for Rowad Modern Engineering, \
a construction company. You are given the user's question, the SQL query that was run, and the \
resulting rows as JSON. Write a clear, concise, natural-language answer for a business user:
- Reference concrete numbers, dates, names and currency codes from the data.
- If there are many rows, summarize patterns/totals rather than listing every single row.
- If the result is empty, say plainly that no matching data was found.
- Do not mention SQL, tables, or column names verbatim; answer in plain business language.
"""


@dataclass
class AgentResult:
    answer: str
    sql: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    attempts: int = 1


class AgentError(Exception):
    """The agent could not produce an answer."""


def _extract_sql(llm_output: str) -> str:
    match = _SQL_FENCE_RE.search(llm_output)
    candidate = match.group(1) if match else llm_output
    return candidate.strip().strip(";").strip()


def _generate_sql(question: str, history_msgs: list[dict]) -> str:
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}, *history_msgs,
                {"role": "user", "content": question}]
    raw = llm.chat(messages, temperature=0.0)
    return _extract_sql(raw)


def _articulate(question: str, sql: str, columns: list[str], rows: list[dict], row_count: int) -> str:
    preview_rows = rows[:50]
    truncated_note = ""
    if row_count > len(preview_rows):
        truncated_note = f"\n(Showing first {len(preview_rows)} of {row_count} rows returned.)"

    user_content = (
        f"Question: {question}\n\n"
        f"SQL executed:\n{sql}\n\n"
        f"Columns: {columns}\n"
        f"Row count: {row_count}\n"
        f"Rows (JSON): {preview_rows}"
        f"{truncated_note}"
    )
    messages = [
        {"role": "system", "content": _ARTICULATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    return llm.chat(messages, temperature=0.2).strip()


def answer_question(question: str) -> AgentResult:
    """Run the full generate -> validate -> execute -> repair -> articulate pipeline."""
    repair_messages: list[dict] = []
    last_error: str | None = None
    retried_empty = False

    for attempt in range(1, settings.sql_max_repair_attempts + 2):
        try:
            if last_error is None:
                sql = _generate_sql(question, repair_messages)
            else:
                repair_messages.append({
                    "role": "user",
                    "content": (
                        f"{last_error}\n"
                        "Reply with a corrected version. Output ONLY the fixed SQL in a ```sql block."
                    ),
                })
                raw = llm.chat(
                    [{"role": "system", "content": _SYSTEM_PROMPT}, *repair_messages],
                    temperature=0.0,
                )
                sql = _extract_sql(raw)

            repair_messages.append({"role": "assistant", "content": f"```sql\n{sql}\n```"})

            safe_sql = validate_and_prepare(sql, settings.sql_max_rows)
            columns, rows = db.run_select(safe_sql, settings.sql_max_rows)

            # A query that runs but returns nothing isn't a SQL error, so the
            # except-block repair loop below never sees it - yet an empty
            # result is often just the model using "=" instead of ILIKE on a
            # name it guessed at. Give it one chance to reconsider before
            # accepting "no data found" as the final answer.
            if len(rows) == 0 and not retried_empty and attempt <= settings.sql_max_repair_attempts:
                retried_empty = True
                last_error = (
                    "Query executed successfully but returned 0 rows. If you used an exact "
                    "match (=) on a name/description column, it was likely too strict - rewrite "
                    "using ILIKE '%...%' for partial/fuzzy matching instead. If you're confident "
                    "0 is genuinely the correct answer, reply with the exact same SQL again."
                )
                logger.info("Attempt %d returned 0 rows, asking model to reconsider fuzzy matching", attempt)
                continue

            answer = _articulate(question, safe_sql, columns, rows, len(rows))
            return AgentResult(
                answer=answer,
                sql=safe_sql,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                attempts=attempt,
            )

        except (SQLValidationError, db.QueryError) as exc:
            last_error = f"That SQL failed with this error:\n{exc}"
            logger.warning("SQL attempt %d failed: %s", attempt, exc)
            continue
        except llm.LLMError as exc:
            raise AgentError(str(exc)) from exc

    raise AgentError(
        f"I couldn't produce a valid query for that question after "
        f"{settings.sql_max_repair_attempts + 1} attempts. Last error: {last_error}"
    )
