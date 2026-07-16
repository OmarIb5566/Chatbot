# Rowad SQL Data Assistant

A natural-language SQL chatbot over Rowad Modern Engineering's data warehouse. Users type plain-English questions; the app generates and validates SQL, runs it against Postgres, and returns a human-readable answer powered by a local Ollama LLM.

## Stack

- **Backend**: FastAPI (Python 3.12), uvicorn
- **Database**: PostgreSQL (external, via tunnel) — tables: `dim_projects`, `fact_ap_check_payments`, `fact_po_followup`
- **LLM**: Ollama (`gemma4:e4b`) running locally, exposed via tunnel
- **Auth**: HTTP Basic Auth, per-user accounts stored in SQLite (`data/app.db`)
- **Chat history**: SQLite (`data/history.db`)

## How to run

```
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

The workflow "Start application" is already configured to run this on port 5000.

## Required secrets (set in Replit Secrets)

| Key | Description |
|-----|-------------|
| `DB_HOST` | Public hostname of your Postgres tunnel |
| `DB_PORT` | Public port of your Postgres tunnel |
| `DB_PASSWORD` | Password for the `rowad_agent` database role |
| `OLLAMA_HOST` | Public HTTPS URL of your Ollama tunnel |
| `BOOTSTRAP_ADMIN_USERNAME` | Username for the first admin account (created on first run if no users exist) |
| `BOOTSTRAP_ADMIN_PASSWORD` | Password for that account |
| `SESSION_SECRET` | Secret key for session signing |

## Non-secret env vars (set in Replit environment)

| Key | Default | Description |
|-----|---------|-------------|
| `DB_NAME` | `data_warehouse` | Database name |
| `DB_USER` | `rowad_agent` | Database user |
| `OLLAMA_MODEL` | `gemma4:e4b` | Ollama model name |
| `SQL_MAX_ROWS` | `200` | Max rows returned per query |
| `SQL_MAX_REPAIR_ATTEMPTS` | `2` | LLM repair attempts on SQL error |
| `DB_STATEMENT_TIMEOUT_MS` | `8000` | Postgres statement timeout |

## User management

Add users after first run:
```
python -m app.manage add-user <username>
```

## Architecture notes

- `app/schema.py` — whitelisted tables and columns the LLM may query
- `app/sql_validator.py` — read-only SQL enforcement via `sqlglot` (defense in depth)
- `app/sql_agent.py` — question → SQL → answer pipeline
- `app/db.py` — connection pool with statement timeout
- `app/auth.py` / `app/history.py` — SQLite-backed auth and chat history
- The app connects to **your machine's** Postgres and Ollama over public tunnels (Cloudflare or ngrok). Keep the tunnels running whenever the chatbot needs to be responsive.

## User preferences

- Keep the existing project structure and stack; do not restructure or migrate.
