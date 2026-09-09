import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.services.startup import seed_sample_policies_if_empty


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        count = seed_sample_policies_if_empty()
        if count:
            logger.info("Auto-seeded %d chunks from sample policies on startup.", count)
    except Exception as exc:
        logger.warning("Startup policy seeding skipped or failed: %s", exc)
    yield


app = FastAPI(
    title="HR Policy Assistant",
    description="Grounded RAG service for HR policies",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(router)