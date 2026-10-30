from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import init_db

settings = get_settings()
configure_logging(settings.log_level)

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests", ["method", "path"])
FRONTEND_DIST = Path("frontend/dist")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Controle de Ciclo de Contratações de Software de Prateleira",
    version="1.0.0",
    description="API para ciclos, softwares, areas, processos, contratos, itens, relatorios e importacao/exportacao.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

if FRONTEND_DIST.exists():
    assets = FRONTEND_DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.middleware("http")
async def count_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
    REQUEST_COUNTER.labels(method=request.method, path=request.url.path).inc()
    return await call_next(request)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str) -> FileResponse:
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    fallback = Path("app/templates/dashboard.html")
    return FileResponse(fallback)
