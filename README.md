# Rowad SQL Data Assistant

A natural-language SQL chatbot over Rowad Modern Engineering's data warehouse
(`dim_projects`, `fact_ap_check_payments`, `fact_po_followup`), answered by a
local Ollama model (`gemma4:e4b`).

## How it works

1. **`app/schema.py`** hard-codes the only 3 tables/columns the agent is
   allowed to see, with their exact (case-sensitive) Postgres column names
   and the join keys back to `dim_projects`.
2. **`app/sql_agent.py`** sends the question + schema to the local LLM, asks
   for a single SELECT statement.
3. **`app/sql_validator.py`** independently re-parses that SQL (via
   `sqlglot`) and rejects anything that isn't a single read-only SELECT/CTE
   touching only the whitelisted tables - defense in depth alongside the
   least-privilege DB role described below. It also caps `LIMIT` and forces
   `NULLS LAST` on `ORDER BY` so NULL aggregates never look like a "top"
   result.
4. **`app/db.py`** executes the query against Postgres with a statement
   timeout, via a connection pool.
5. If execution fails, the error is fed back to the LLM for up to
   `SQL_MAX_REPAIR_ATTEMPTS` corrections.
6. On success, the rows are handed back to the LLM to articulate a plain-
   language answer.

Exposed via FastAPI: `POST /chat {"question": "..."}`, `GET /health`, plus
`GET /conversations`, `GET /conversations/{id}`, `DELETE /conversations/{id}`,
and `GET /me` for the per-user chat history described below. Every route
except `/health` requires a logged-in user.

## Local dev setup

A local Postgres (Docker) restored from `Data_Warehouse.backup` stands in for
the real data warehouse during development:

```
docker compose up -d
MSYS_NO_PATHCONV=1 docker exec rowad-postgres pg_restore -U rowad -d data_warehouse \
    --no-owner --no-privileges -j 4 /tmp/Data_Warehouse.backup   # after docker cp'ing the file in
```

A least-privilege role `rowad_agent` was created in that database, granted
`SELECT` on only the 3 whitelisted tables, and set to
`default_transaction_read_only = on`. `.env` points the app at this role.
**Do the same on the real production database before pointing this app at
it** - never connect the app with a superuser/admin credential.

## Running

```
uv sync
uv run uvicorn app.main:app --reload --port 8010
```

Requires a local Ollama server with `gemma4:e4b` pulled (`ollama pull gemma4:e4b`).

## User accounts

This serves real Rowad business data, so every route except `/health` is
gated behind a per-user account (HTTP Basic Auth, checked against a `users`
table in `data/app.db` - separate from the read-only warehouse connection).
Each user's chat history is private to their own account.

On first run, if no accounts exist yet, `BOOTSTRAP_ADMIN_USERNAME` /
`BOOTSTRAP_ADMIN_PASSWORD` (from `.env`) create one so you're never locked
out. After that, manage accounts with:

```
uv run python -m app.manage add-user alice     # prompts for a password
uv run python -m app.manage list-users
uv run python -m app.manage remove-user alice
```

Passwords are stored as salted PBKDF2 hashes, never in plaintext.

## Configuration

Copy `.env.example` to `.env` and fill in real values for production:
`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` should point at the
real warehouse with a read-only role scoped to the 3 tables above;
`OLLAMA_HOST`/`OLLAMA_MODEL` point at wherever Ollama runs `gemma4:e4b`.

## Tests

```
uv run pytest tests/ -v
```

Covers the SQL validator (table whitelist, DML/DDL rejection, single-
statement enforcement, LIMIT capping, NULLS LAST enforcement). These run
without a database or LLM.

## Hosting on Replit for a small group of users

This serves real Rowad business data, so the app is gated behind per-user
accounts (see "User accounts" above) - only give the URL to people who
should see this data, and create each of them their own account.

Ollama and Postgres stay on your own machine (nothing about the data or the
model changes) - Replit only hosts the FastAPI app, which reaches your
machine over two tunnels. You need to do the following yourself (these steps
require your own Replit/Cloudflare accounts and can't be scripted from here):

1. **Tunnel your local Ollama and Postgres to the internet.** A free
   [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
   (`cloudflared`) run from this machine can expose both:
   - Ollama (`http://localhost:11434`) as an HTTPS hostname.
   - Postgres (`localhost:5433`) as a TCP tunnel.
   ngrok is a simpler alternative if you don't want to set up a Cloudflare
   Zero Trust account, but its free tier historically limits you to one
   tunnel at a time - check current limits before relying on it for both
   services at once. Keep this machine and the tunnel running whenever the
   hosted chatbot needs to answer questions.

2. **Import this repo into a new Repl** (Replit -> Create -> Import from
   GitHub, or upload the folder). The included `.replit` file tells Replit
   how to run the app: `uv sync && uv run uvicorn app.main:app --host 0.0.0.0
   --port $PORT`.

3. **Set these as Replit "Secrets"** (not committed to `.env`):
   - `DB_HOST` / `DB_PORT` - your Postgres tunnel's public host/port.
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD` - unchanged, still `rowad_agent`.
   - `OLLAMA_HOST` - your Ollama tunnel's public HTTPS URL.
   - `OLLAMA_MODEL`, `SQL_MAX_ROWS`, `SQL_MAX_REPAIR_ATTEMPTS` - same as local.
   - `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD` - creates your
     first account; add everyone else with `uv run python -m app.manage add-user`.

4. **Deploy** using Replit's Deployments feature (Reserved VM keeps it
   always-on; Autoscale is cheaper but cold-starts). Share the deployment
   URL only with people you've created an account for.

Because the LLM and DB calls now cross the internet through your tunnels,
expect slower responses than running everything locally, and expect the
hosted chatbot to go down if your machine, Ollama, Postgres, or either
tunnel goes offline.

## Known model limitations

`gemma4:e4b` is a small local model - it won't always produce optimal SQL
(e.g. it may skip an ORDER BY tie-break, or over/under-join). The validator
only guarantees *safety* (read-only, whitelisted tables), not query
optimality. If you see a wrong-looking answer, check the `sql` field
returned by `/chat` - that's the exact query that ran.
