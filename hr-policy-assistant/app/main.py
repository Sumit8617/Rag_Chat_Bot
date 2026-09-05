from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(
    title="HR Policy Assistant",
    description="Grounded RAG service for HR policies",
    version="1.0.0"
)


app.include_router(router)