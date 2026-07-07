import base64
import binascii
import logging
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from app import auth, db, history, llm
from app.config import settings
from app.sql_agent import AgentError, answer_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_title)
auth.init_db()
history.init_db()

_GUEST_COOKIE = "guest_id"
_GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


class IdentityMiddleware(BaseHTTPMiddleware):
    """Attach an identity to every request except /health - never blocks.

    Logged-in users are identified by an `Authorization: Basic ...` header
    the frontend's own login form sends manually (not a browser-native
    prompt), so nobody is forced to log in. Anyone without valid credentials
    is treated as a guest, identified by a random cookie so their chat
    history still persists across requests in the same browser.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        username = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[len("Basic "):]).decode("utf-8")
                candidate_user, _, candidate_pass = decoded.partition(":")
            except (binascii.Error, UnicodeDecodeError):
                candidate_user = candidate_pass = ""
            if candidate_user and auth.verify_user(candidate_user, candidate_pass):
                username = candidate_user

        is_guest = username is None
        new_guest_id = None
        if is_guest:
            guest_id = request.cookies.get(_GUEST_COOKIE)
            if not guest_id:
                guest_id = secrets.token_hex(16)
                new_guest_id = guest_id
            username = f"guest:{guest_id}"

        request.state.username = username
        request.state.is_guest = is_guest

        response = await call_next(request)
        if new_guest_id:
            response.set_cookie(
                _GUEST_COOKIE, new_guest_id, max_age=_GUEST_COOKIE_MAX_AGE, httponly=True, samesite="lax"
            )
        return response


app.add_middleware(IdentityMiddleware)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sql: str
    row_count: int
    columns: list[str]
    rows: list[dict]
    conversation_id: int


@app.get("/health")
def health():
    db_ok = db.health_check()
    llm_ok = llm.health_check()
    status = "ok" if db_ok and llm_ok else "degraded"
    return {
        "status": status,
        "database": "ok" if db_ok else "unreachable",
        "llm": "ok" if llm_ok else f"unreachable or model '{settings.ollama_model}' not pulled",
    }


@app.get("/me")
def me(request: Request):
    return {"username": None if request.state.is_guest else request.state.username, "is_guest": request.state.is_guest}


@app.post("/login")
def login(payload: LoginRequest):
    if not auth.verify_user(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"username": payload.username}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request):
    username = request.state.username

    if payload.conversation_id is not None:
        if not history.conversation_exists(payload.conversation_id, username):
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id = payload.conversation_id
    else:
        conversation_id = history.create_conversation(username, payload.question)

    history.add_message(conversation_id, "user", payload.question)

    try:
        result = answer_question(payload.question)
    except AgentError as exc:
        history.add_message(conversation_id, "assistant", f"Error: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    history.add_message(conversation_id, "assistant", result.answer, result.sql)

    return ChatResponse(
        answer=result.answer,
        sql=result.sql,
        row_count=result.row_count,
        columns=result.columns,
        rows=result.rows,
        conversation_id=conversation_id,
    )


@app.get("/conversations")
def list_conversations(request: Request):
    return history.list_conversations(request.state.username)


@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, request: Request):
    conversation = history.get_conversation(conversation_id, request.state.username)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, request: Request):
    if not history.delete_conversation(conversation_id, request.state.username):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
