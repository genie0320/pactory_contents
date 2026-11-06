"""Pactory Studio Headless REST API Application.

Stateless FastAPI backend serving multi-platform drafting, synthesis,
proofreading, and indexing capabilities.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.auth import LoginRequest, LoginResponse, get_configured_password
from src.api.routers import editor, generator, inbox, style
from src.exceptions import LLMServiceError, PactoryError

app = FastAPI(
    title="Pactory Studio API",
    description="Headless editorial synthesis, seed retrieval, and proofreading engine.",
    version="2.0.0",
)

# -------------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Exception Handlers
# -------------------------------------------------------------
@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "error_type": "LLMServiceError"},
    )


@app.exception_handler(PactoryError)
async def pactory_error_handler(request: Request, exc: PactoryError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "error_type": "PactoryError"},
    )


# -------------------------------------------------------------
# Core & Auth Endpoints
# -------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0", "service": "pactory-studio"}


@app.get("/api/auth/status")
async def auth_status():
    """Check if studio password authentication is required."""
    pwd = get_configured_password()
    return {"auth_required": bool(pwd)}


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Authenticate with studio password."""
    configured_pwd = get_configured_password()
    if not configured_pwd or req.password == configured_pwd:
        return LoginResponse(authenticated=True, message="인증에 성공했습니다.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="비밀번호가 일치하지 않습니다.",
    )


# -------------------------------------------------------------
# Routers Registration
# -------------------------------------------------------------
app.include_router(inbox.router, prefix="/api")
app.include_router(generator.router, prefix="/api")
app.include_router(editor.router, prefix="/api")
app.include_router(style.router, prefix="/api")


# -------------------------------------------------------------
# Frontend Static Build Mount (For Single-Port Serving on 8501)
# -------------------------------------------------------------
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API routes through
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root_placeholder():
        return {
            "message": "Pactory Studio Headless REST API is running.",
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
        }
