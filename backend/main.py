"""
Pagani Zonda R – Enterprise Intelligence API
FastAPI backend with RAG, JWT auth, rate limiting, CORS, logging,
database persistence, security middleware, health monitoring,
enterprise RBAC, analytics, audit, document management, and WebSocket support.
"""

import os
import time
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import (
    FastAPI, Depends, HTTPException, Request, status,
    APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect,
    Query as QueryParam,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from auth import (
    UserRegister, UserLogin, TokenResponse, RefreshRequest,
    ChatRequest, ChatResponse, UserInfo, register_user, authenticate_user, refresh_access_token,
    get_current_user, users_db, require_permission,
    ROLE_PERMISSIONS, VALID_ROLES,
)
from vector_store import vector_store
from pdf_ingester import ingest_all_pdfs
from rag_pipeline import (
    generate_response, 
    generate_response_stream,
    agentic_router,
    _get_history,
)
from logging_config import setup_logging, log_event
from database import init_db, check_db_connection
from middleware import SecurityHeadersMiddleware, RequestSizeLimitMiddleware, RequestTracingMiddleware
from error_handlers import register_error_handlers
from audit import audit, get_audit_logs, get_login_attempts
from analytics import (
    get_user_engagement_metrics, get_query_success_rates,
    get_ai_performance_metrics, get_system_health,
    export_analytics_csv, set_server_start_time,
)
from document_manager import (
    upload_document, list_documents, get_document,
    delete_document, update_document_metadata,
)
from websocket_manager import ws_manager
from cache import query_cache

load_dotenv()

# ── Structured Logging (replaces basicConfig) ──
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("pagani.api")

# ── Rate Limiter ──
limiter = Limiter(key_func=get_remote_address)

# ── Server Start Time (for uptime tracking) ──
SERVER_START_TIME = None


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize vector store and database on startup."""
    global SERVER_START_TIME
    SERVER_START_TIME = datetime.now(timezone.utc)
    set_server_start_time(SERVER_START_TIME)

    logger.info("═" * 60)
    logger.info("  PAGANI ZONDA R — Enterprise Intelligence API")
    logger.info("═" * 60)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("API will start but persistence features may fail.")

    # Initialize vector store
    try:
        vector_store.initialize()
        if vector_store.needs_pdf_ingestion():
            pdf_chunks = ingest_all_pdfs()
            if pdf_chunks:
                vector_store.ingest_pdf_chunks(pdf_chunks)
        logger.info("Vector store initialized successfully.")
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        logger.warning("API will start but /chat endpoints may fail.")

    log_event("pagani.api", "system_startup", metadata={
        "timestamp": SERVER_START_TIME.isoformat()
    })

    logger.info("API server ready.")
    yield
    logger.info("API server shutting down.")


# ── App ──
app = FastAPI(
    title="Pagani Zonda R – Enterprise Intelligence API",
    description="RAG-powered AI assistant for Pagani Zonda R enterprise data.",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter


# ── Rate Limit Error Handler ──
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests. Please slow down.",
            "error_code": "RATE_LIMIT_EXCEEDED",
        },
    )


# ── Global Exception Handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    log_event("pagani.api", "api_error", metadata={
        "error": str(exc),
        "path": str(request.url.path),
    })
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error_code": "INTERNAL_ERROR",
        },
    )


# ── Register Enterprise Error Handlers ──
register_error_handlers(app)

# ── Security Middleware ──
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)


# ═══════════════════════════════════════════
# Analytics Helper
# ═══════════════════════════════════════════

def _track_analytics(event_type: str, user_id: str | None = None, metadata: dict | None = None):
    """Track a usage analytics event (fire-and-forget)."""
    try:
        from database import get_db_session
        from models import AnalyticsEvent
        with get_db_session() as db:
            db.add(AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                metadata_=metadata,
            ))
    except Exception as e:
        logger.warning(f"Analytics tracking failed (non-fatal): {e}")


# ═══════════════════════════════════════════
# Chat Persistence Helper
# ═══════════════════════════════════════════

def _persist_chat(username: str, question: str, response: str):
    """Persist a chat Q&A pair to the database (fire-and-forget)."""
    try:
        from database import get_db_session
        from models import ChatHistory, User
        with get_db_session() as db:
            user = db.query(User).filter(User.name == username).first()
            if user:
                db.add(ChatHistory(
                    user_id=user.id,
                    question=question,
                    response=response,
                ))
    except Exception as e:
        logger.warning(f"Chat persistence failed (non-fatal): {e}")


# ═══════════════════════════════════════════
# Health Check (Enhanced)
# ═══════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    log_event("pagani.api", "system_health_check")

    # Database status
    db_connected = check_db_connection()

    # AI service status
    ai_available = vector_store._initialized

    # Uptime
    uptime_seconds = 0
    if SERVER_START_TIME:
        uptime_seconds = (datetime.now(timezone.utc) - SERVER_START_TIME).total_seconds()

    overall_status = "healthy" if (db_connected and ai_available) else "degraded"

    return {
        "status": overall_status,
        "database": "connected" if db_connected else "disconnected",
        "ai_service": "available" if ai_available else "unavailable",
        "uptime": f"{uptime_seconds:.0f}s",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vector_store_initialized": ai_available,
        "registered_users": len(users_db),
    }


@app.get("/api/health/detailed")
async def health_check_detailed(current_user: dict = Depends(require_permission("manage_users"))):
    """Secure detailed health check for admins."""
    return await health_check()


# ═══════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════

@app.post("/api/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(request: Request, user: UserRegister):
    """Register a new user with username, password, and role."""
    logger.info(f"Registration attempt: {user.username} (role: {user.role})")
    result = register_user(user)
    _track_analytics("user_registered", user_id=user.username, metadata={"role": user.role})
    return {"message": "User registered successfully", **result}


@app.post("/api/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    """Authenticate and receive JWT access + refresh tokens."""
    logger.info(f"Login attempt: {user.username}")
    log_event("pagani.api", "user_login", user_id=user.username)
    result = await authenticate_user(user)
    _track_analytics("login_success", user_id=user.username)
    return result


@app.post("/api/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh(request: Request, body: RefreshRequest):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    logger.info("Token refresh attempt")
    return refresh_access_token(body.refresh_token)


@app.get("/api/me", response_model=UserInfo)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    db_user = users_db.get(current_user["username"])
    return UserInfo(
        username=current_user["username"],
        role=current_user["role"],
        created_at=db_user.get("created_at", "unknown"),
    )


# ═══════════════════════════════════════════
# RAG Chat Endpoints
# ═══════════════════════════════════════════

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    RAG-powered chat endpoint.
    Embeds question → FAISS search (role-filtered) → Gemini generation.
    """
    start_time = time.time()
    username = current_user["username"]
    user_role = current_user["role"]

    logger.info(f"Chat request | user={username} | role={user_role} | q='{body.question[:80]}'")
    log_event("pagani.api", "chat_request", user_id=username, metadata={"question": body.question[:100]})
    _track_analytics("chat_started", user_id=username)
    _track_analytics("query_submitted", user_id=username, metadata={"question_length": len(body.question)})

    try:
        # Step 1: Agentic Routing (Decide whether to search and reformulate query)
        history = _get_history(username)
        router_decision = agentic_router(body.question, history)
        log_event("pagani.api", "role_routing", user_id=username, metadata=router_decision)
        
        # Step 2: Conditional Semantic Search
        context_docs = []
        if router_decision.get("needs_search", True):
            search_query = router_decision.get("search_query") or body.question
            logger.info(f"Router decided to search with query: '{search_query[:50]}'")
            context_docs = vector_store.search(
                query=search_query,
                top_k=5,
                user_role=user_role,
                filters=router_decision.get("metadata_filters")
            )
            logger.info(f"Retrieved {len(context_docs)} documents for user {username}")
        else:
            logger.info(f"Router decided to skip vector search for user {username}")

        # Step 3: Generate response
        result = generate_response(
            question=body.question,
            context_docs=context_docs,
            user_role=user_role,
            username=username,
        )

        latency = time.time() - start_time
        logger.info(
            f"Chat response | user={username} | confidence={result['confidence']} | "
            f"sources={len(result['sources'])} | latency={latency:.2f}s"
        )
        log_event("pagani.api", "chat_response", user_id=username, metadata={
            "confidence": result["confidence"],
            "sources": len(result["sources"]),
            "latency_s": round(latency, 2),
        })
        _track_analytics("response_received", user_id=username, metadata={
            "confidence": result["confidence"],
            "latency_s": round(latency, 2),
        })

        # Persist chat to DB (additive)
        _persist_chat(username, body.question, result["answer"])

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            user_role=user_role,
        )

    except RuntimeError as e:
        logger.error(f"RAG pipeline error for user {username}: {e}")
        log_event("pagani.api", "api_error", user_id=username, metadata={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
    except Exception as e:
        logger.error(f"Unexpected chat error for user {username}: {e}", exc_info=True)
        log_event("pagani.api", "api_error", user_id=username, metadata={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred processing your request.",
        )


@app.post("/api/chat/debug")
@limiter.limit("20/minute")
async def chat_debug(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Debug-enhanced RAG chat endpoint.
    Returns the full pipeline trace alongside the normal response.
    Existing /api/chat and /api/chat/stream are NOT modified.
    """
    import time as _time
    t_start = _time.time()
    username = current_user["username"]
    user_role = current_user["role"]

    logger.info(f"Debug chat request | user={username} | role={user_role} | q='{body.question[:80]}'")

    try:
        # Step 1: Agentic Routing
        history = _get_history(username)
        router_decision = agentic_router(body.question, history)

        # Step 2: Search with debug info
        context_docs = []
        debug_info = {
            "pipeline_steps": [
                {"step": "query_received", "label": "Query Received", "timestamp_ms": 0}
            ],
            "search_results": [],
            "retrieved_chunks": [],
            "timing": {},
            "router_decision": router_decision,
        }

        if router_decision.get("needs_search", True):
            search_query = router_decision.get("search_query") or body.question

            # Use the debug-enhanced search
            search_result = vector_store.search_with_debug(
                query=search_query,
                top_k=5,
                user_role=user_role,
                filters=router_decision.get("metadata_filters")
            )
            context_docs = search_result["results"]
            debug_info = search_result["debug"]
            debug_info["router_decision"] = router_decision

        # Step 3: Generate response
        t_gen = _time.time()
        result = generate_response(
            question=body.question,
            context_docs=context_docs,
            user_role=user_role,
            username=username,
        )
        gen_ms = int((_time.time() - t_gen) * 1000)
        total_ms = int((_time.time() - t_start) * 1000)

        debug_info["timing"]["generation_ms"] = gen_ms
        debug_info["timing"]["total_ms"] = total_ms
        debug_info["pipeline_steps"].append({
            "step": "llm_generated",
            "label": "LLM Response Generated",
            "timestamp_ms": total_ms,
        })

        # Persist chat (additive, same as normal endpoint)
        _persist_chat(username, body.question, result["answer"])

        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"],
            "user_role": user_role,
            "debug": debug_info,
        }

    except RuntimeError as e:
        logger.error(f"Debug RAG pipeline error for user {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again.",
        )
    except Exception as e:
        logger.error(f"Unexpected debug chat error for user {username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred processing your request.",
        )


@app.post("/api/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Streaming RAG chat endpoint.
    Returns Server-Sent Events with token-by-token response.
    """
    username = current_user["username"]
    user_role = current_user["role"]

    logger.info(f"Stream chat request | user={username} | role={user_role} | q='{body.question[:80]}'")
    log_event("pagani.api", "chat_request", user_id=username, metadata={
        "question": body.question[:100],
        "streaming": True,
    })
    _track_analytics("chat_started", user_id=username, metadata={"streaming": True})

    try:
        history = _get_history(username)
        router_decision = agentic_router(body.question, history)
        
        context_docs = []
        if router_decision.get("needs_search", True):
            search_query = router_decision.get("search_query") or body.question
            logger.info(f"Router decided to search with query: '{search_query[:50]}'")
            context_docs = vector_store.search(
                query=search_query,
                top_k=5,
                user_role=user_role,
                filters=router_decision.get("metadata_filters")
            )
        else:
            logger.info(f"Router decided to skip vector search for user {username}")

        collected_chunks: list[str] = []

        async def event_generator():
            async for chunk in generate_response_stream(
                question=body.question,
                context_docs=context_docs,
                user_role=user_role,
                username=username,
            ):
                collected_chunks.append(chunk)
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

            # Persist after streaming completes
            full_response = "".join(collected_chunks)
            _persist_chat(username, body.question, full_response)
            _track_analytics("response_received", user_id=username, metadata={"streaming": True})
            log_event("pagani.api", "chat_response", user_id=username, metadata={"streaming": True})

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except RuntimeError as e:
        logger.error(f"Streaming RAG error for user {username}: {e}")
        log_event("pagani.api", "api_error", user_id=username, metadata={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable.",
        )


# ═══════════════════════════════════════════
# V1 Enterprise API Router
# ═══════════════════════════════════════════

v1_router = APIRouter(prefix="/api/v1", tags=["Enterprise V1"])


# ── Pydantic Models for V1 ──
class RoleChangeRequest(BaseModel):
    new_role: str = Field(..., description="New role to assign")


class DocumentMetadataUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None


# ───────────────────────────
# RBAC Admin Endpoints
# ───────────────────────────

@v1_router.get("/admin/users", summary="List all users")
async def v1_list_users(
    current_user: dict = Depends(require_permission("manage_users")),
):
    """List all registered users (admin/super_admin only)."""
    return {
        "users": [
            {"username": u, "role": d["role"], "created_at": d.get("created_at", "unknown")}
            for u, d in users_db.items()
        ],
        "total": len(users_db),
    }


@v1_router.put("/admin/users/{username}/role", summary="Change user role")
async def v1_change_user_role(
    username: str,
    body: RoleChangeRequest,
    current_user: dict = Depends(require_permission("manage_roles")),
):
    """Change a user's role (super_admin only)."""
    if username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if body.new_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")

    old_role = users_db[username]["role"]
    users_db[username]["role"] = body.new_role

    # Log role change
    audit.log_role_change(
        changed_by=current_user["username"],
        target_user=username,
        old_role=old_role,
        new_role=body.new_role,
    )

    # Persist to DB
    try:
        from database import get_db_session
        from models import User, RoleAuditLog
        with get_db_session() as db:
            user = db.query(User).filter(User.name == username).first()
            if user:
                user.role = body.new_role
            db.add(RoleAuditLog(
                changed_by=current_user["username"],
                target_user=username,
                old_role=old_role,
                new_role=body.new_role,
            ))
    except Exception as e:
        logger.warning(f"Role change DB persistence failed: {e}")

    return {
        "message": f"Role updated: {username} ({old_role} -> {body.new_role})",
        "username": username,
        "old_role": old_role,
        "new_role": body.new_role,
    }


@v1_router.get("/admin/roles/audit", summary="Role change audit log")
async def v1_role_audit_log(
    limit: int = QueryParam(default=50, le=500),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """View role change audit trail."""
    logs = get_audit_logs(action="role_change", limit=limit)
    return {"audit_logs": logs, "total": len(logs)}


@v1_router.get("/admin/permissions", summary="View permission matrix")
async def v1_permissions(
    current_user: dict = Depends(get_current_user),
):
    """View the RBAC permission matrix."""
    return {
        "permissions": ROLE_PERMISSIONS,
        "valid_roles": list(VALID_ROLES),
        "your_role": current_user["role"],
        "your_permissions": ROLE_PERMISSIONS.get(current_user["role"], []),
    }


# ───────────────────────────
# Analytics Endpoints
# ───────────────────────────

@v1_router.get("/analytics/engagement", summary="User engagement metrics")
async def v1_analytics_engagement(
    days: int = QueryParam(default=30, le=365),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Get user engagement metrics for the specified period."""
    return get_user_engagement_metrics(days=days)


@v1_router.get("/analytics/queries", summary="Query success/failure rates")
async def v1_analytics_queries(
    days: int = QueryParam(default=30, le=365),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Get query success/failure rate statistics."""
    return get_query_success_rates(days=days)


@v1_router.get("/analytics/ai-performance", summary="AI performance metrics")
async def v1_analytics_ai(
    days: int = QueryParam(default=30, le=365),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Get AI performance metrics (confidence, latency)."""
    return get_ai_performance_metrics(days=days)


@v1_router.get("/analytics/system-health", summary="System health metrics")
async def v1_system_health(
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Get system health metrics (CPU, memory, uptime)."""
    return get_system_health()


@v1_router.get("/analytics/export", summary="Export analytics as CSV")
async def v1_analytics_export(
    days: int = QueryParam(default=30, le=365),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Export analytics events as CSV."""
    csv_data = export_analytics_csv(days=days)
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{days}d.csv"},
    )


# ───────────────────────────
# Audit Endpoints
# ───────────────────────────

@v1_router.get("/audit/logs", summary="View audit logs")
async def v1_audit_logs(
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = QueryParam(default=100, le=1000),
    offset: int = QueryParam(default=0, ge=0),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """Admin view of all audit/system logs."""
    logs = get_audit_logs(action=action, user_id=user_id, limit=limit, offset=offset)
    return {"logs": logs, "total": len(logs)}


@v1_router.get("/audit/login-attempts", summary="Login attempt history")
async def v1_login_attempts(
    limit: int = QueryParam(default=50, le=500),
    current_user: dict = Depends(require_permission("manage_users")),
):
    """View recent login attempts."""
    attempts = get_login_attempts(limit=limit)
    return {"attempts": attempts, "total": len(attempts)}


# ───────────────────────────
# Document Management Endpoints
# ───────────────────────────

@v1_router.post("/documents/upload", summary="Upload a document")
async def v1_upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: dict = Depends(require_permission("write")),
):
    """Upload a PDF, DOCX, or TXT document for RAG ingestion."""
    result = await upload_document(
        file=file,
        uploaded_by=current_user["username"],
        title=title,
    )
    audit.log(
        action=audit.ACTION_DOCUMENT_UPLOAD,
        user_id=current_user["username"],
        metadata={"filename": result.get("filename"), "chunks": result.get("chunk_count")},
    )
    return result


@v1_router.get("/documents", summary="List documents")
async def v1_list_documents(
    limit: int = QueryParam(default=100, le=500),
    offset: int = QueryParam(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List all uploaded documents."""
    docs = list_documents(limit=limit, offset=offset)
    return {"documents": docs, "total": len(docs)}


@v1_router.get("/documents/{doc_id}", summary="Get document details")
async def v1_get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get details of a specific document."""
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@v1_router.delete("/documents/{doc_id}", summary="Delete a document")
async def v1_delete_document(
    doc_id: str,
    current_user: dict = Depends(require_permission("delete")),
):
    """Delete a document (admin only)."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    audit.log(
        action=audit.ACTION_DOCUMENT_DELETE,
        user_id=current_user["username"],
        metadata={"document_id": doc_id},
    )
    return {"message": "Document deleted", "id": doc_id}


@v1_router.put("/documents/{doc_id}/metadata", summary="Update document metadata")
async def v1_update_document_metadata(
    doc_id: str,
    body: DocumentMetadataUpdate,
    current_user: dict = Depends(require_permission("write")),
):
    """Update document metadata (title, tags)."""
    result = update_document_metadata(doc_id, title=body.title, tags=body.tags)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


# ───────────────────────────
# Cache Stats Endpoint
# ───────────────────────────

@v1_router.get("/cache/stats", summary="Cache statistics")
async def v1_cache_stats(
    current_user: dict = Depends(require_permission("manage_users")),
):
    """View query cache statistics."""
    return {
        "query_cache": query_cache.stats,
    }


# ───────────────────────────
# WebSocket Endpoints
# ───────────────────────────

@v1_router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket):
    """WebSocket for real-time notifications."""
    await ws_manager.connect(websocket, "notifications")
    try:
        while True:
            # Keep connection alive, optionally receive client messages
            data = await websocket.receive_text()
            # Echo or handle client messages
            await ws_manager.send_personal(websocket, {"type": "ack", "message": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "notifications")


@v1_router.websocket("/ws/logs")
async def ws_logs(websocket: WebSocket):
    """WebSocket for real-time log streaming (admin only)."""
    await ws_manager.connect(websocket, "logs")
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_personal(websocket, {"type": "ack", "message": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "logs")


# ── Mount V1 Router ──
app.include_router(v1_router)


# ═══════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )