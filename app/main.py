import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.config import get_settings
from app.database import init_db
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not get_settings().disable_scheduler:
        start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Bookdrop", lifespan=lifespan)
app.include_router(api_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
