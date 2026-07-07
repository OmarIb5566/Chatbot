# Graph Report - d:/Model/Chatbot  (2026-07-06)

## Corpus Check
- Corpus is ~3,630 words - fits in a single context window. You may not need a graph.

## Summary
- 81 nodes · 155 edges · 16 communities (9 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.76)
- Token cost: 59,670 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_SQL Validator & Tests|SQL Validator & Tests]]
- [[_COMMUNITY_SQL Agent  LLM Pipeline|SQL Agent / LLM Pipeline]]
- [[_COMMUNITY_DB Execution & Health Checks|DB Execution & Health Checks]]
- [[_COMMUNITY_Chat API Endpoint|Chat API Endpoint]]
- [[_COMMUNITY_Infra & Config Setup|Infra & Config Setup]]
- [[_COMMUNITY_Whitelisted Schema Definition|Whitelisted Schema Definition]]
- [[_COMMUNITY_SQL Safety Rules|SQL Safety Rules]]
- [[_COMMUNITY_dim_projects Table|dim_projects Table]]
- [[_COMMUNITY_fact_ap_check_payments Table|fact_ap_check_payments Table]]
- [[_COMMUNITY_fact_po_followup Table|fact_po_followup Table]]
- [[_COMMUNITY_Table Column Lookup|Table Column Lookup]]
- [[_COMMUNITY_Answer Articulation Prompt|Answer Articulation Prompt]]
- [[_COMMUNITY_Forbidden SQL Functions|Forbidden SQL Functions]]
- [[_COMMUNITY_Project Package Manifest|Project Package Manifest]]

## God Nodes (most connected - your core abstractions)
1. `validate_and_prepare()` - 25 edges
2. `answer_question()` - 17 edges
3. `SQLValidationError` - 16 edges
4. `AgentError` - 9 edges
5. `Settings (app config)` - 8 edges
6. `chat() (llm)` - 8 edges
7. `chat() endpoint` - 8 edges
8. `run_select()` - 7 edges
9. `get_pool()` - 6 edges
10. `QueryError` - 5 edges

## Surprising Connections (you probably didn't know these)
- `postgres service (docker-compose)` --shares_data_with--> `Settings (app config)`  [INFERRED]
  docker-compose.yml → app/config.py
- `Project manifest (rowad-sql-agent)` --conceptually_related_to--> `chat() (llm)`  [INFERRED]
  pyproject.toml → app/llm.py
- `Project manifest (rowad-sql-agent)` --conceptually_related_to--> `chat() endpoint`  [INFERRED]
  pyproject.toml → app/main.py
- `Project manifest (rowad-sql-agent)` --conceptually_related_to--> `validate_and_prepare()`  [INFERRED]
  pyproject.toml → app/sql_validator.py
- `Project manifest (rowad-sql-agent)` --conceptually_related_to--> `Settings (app config)`  [INFERRED]
  pyproject.toml → app/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Layered defense-in-depth SQL safety pipeline** — app_sql_agent_answer_question, app_sql_validator_validate_and_prepare, app_db_run_select, app_schema_tables [INFERRED 0.85]
- **Per-module domain exception pattern** — app_db_query_error, app_llm_error, app_sql_validator_sql_validation_error, app_sql_agent_agent_error [INFERRED 0.80]
- **Generate-validate-execute-repair loop** — app_sql_agent_answer_question, app_sql_agent_generate_sql, app_sql_validator_validate_and_prepare, app_db_run_select [EXTRACTED 1.00]

## Communities (16 total, 7 thin omitted)

### Community 0 - "SQL Validator & Tests"
Cohesion: 0.23
Nodes (18): Generated SQL failed safety validation., SQLValidationError, validate_and_prepare(), Defense-in-depth validation rationale, SQL validator test suite, test_allows_cte(), test_allows_join_across_whitelisted_tables(), test_allows_simple_select() (+10 more)

### Community 1 - "SQL Agent / LLM Pipeline"
Cohesion: 0.26
Nodes (11): chat() (llm), LLMError, The local Ollama LLM could not be reached or returned an error., Send a chat completion request to the local Ollama server., AgentResult, answer_question(), _articulate(), _extract_sql() (+3 more)

### Community 2 - "DB Execution & Health Checks"
Cohesion: 0.24
Nodes (10): health_check() (db), QueryError, A SQL statement failed to execute against Postgres., Execute a single read-only SELECT and return (columns, rows).      Any failure r, run_select(), health_check() (llm), FastAPI app instance, health() endpoint (+2 more)

### Community 3 - "Chat API Endpoint"
Cohesion: 0.46
Nodes (7): chat() endpoint, ChatRequest, ChatResponse, AgentError, The agent could not produce an answer., ask() JS function, BaseModel

### Community 4 - "Infra & Config Setup"
Cohesion: 0.33
Nodes (7): Settings (app config), get_pool(), BaseSettings, postgres service (docker-compose), Project manifest (rowad-sql-agent), Least-privilege DB role rationale, ThreadedConnectionPool

### Community 5 - "Whitelisted Schema Definition"
Cohesion: 0.29
Nodes (6): ColumnDef, Whitelisted schema for the SQL agent.  Only these 3 tables/columns may ever be t, render_schema_for_prompt(), TableDef, TABLES whitelist dict, _SYSTEM_PROMPT

### Community 6 - "SQL Safety Rules"
Cohesion: 0.40
Nodes (5): _cap_row_limit(), _default_nulls_last(), Defense-in-depth validation for LLM-generated SQL.  The DB role the app connects, Postgres defaults DESC ordering to NULLS FIRST, which makes rows with a     NULL, Expression

## Knowledge Gaps
- **12 isolated node(s):** `ColumnDef`, `TableDef`, `rowad-sql-agent`, `DIM_PROJECTS`, `FACT_AP_CHECK_PAYMENTS` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `validate_and_prepare()` connect `SQL Validator & Tests` to `SQL Agent / LLM Pipeline`, `DB Execution & Health Checks`, `Infra & Config Setup`, `Whitelisted Schema Definition`, `SQL Safety Rules`?**
  _High betweenness centrality (0.285) - this node is a cross-community bridge._
- **Why does `answer_question()` connect `SQL Agent / LLM Pipeline` to `SQL Validator & Tests`, `DB Execution & Health Checks`, `Chat API Endpoint`, `Infra & Config Setup`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `SQLValidationError` connect `SQL Validator & Tests` to `SQL Agent / LLM Pipeline`, `Chat API Endpoint`, `SQL Safety Rules`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `SQLValidationError` (e.g. with `AgentError` and `AgentResult`) actually correct?**
  _`SQLValidationError` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `AgentError` (e.g. with `ChatRequest` and `ChatResponse`) actually correct?**
  _`AgentError` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Settings (app config)` (e.g. with `postgres service (docker-compose)` and `Project manifest (rowad-sql-agent)`) actually correct?**
  _`Settings (app config)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `A SQL statement failed to execute against Postgres.`, `Execute a single read-only SELECT and return (columns, rows).      Any failure r`, `The local Ollama LLM could not be reached or returned an error.` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._