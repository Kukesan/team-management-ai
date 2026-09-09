from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.core.logging import configure_logging
from app.db.pool import close_pool, create_pool
from app.dependencies import verify_internal_api_key
from app.routers import chat, help, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await create_pool()
    yield
    await close_pool()


app = FastAPI(title="team-management-ai", lifespan=lifespan)

# No CORS middleware: this service is never called from a browser, only
# server-to-server by team-management-api's AiController/AiService. Adding
# CORSMiddleware here would be dead config for a problem that doesn't exist.

app.include_router(chat.router, dependencies=[Depends(verify_internal_api_key)])
app.include_router(summary.router, dependencies=[Depends(verify_internal_api_key)])
app.include_router(help.router, dependencies=[Depends(verify_internal_api_key)])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
