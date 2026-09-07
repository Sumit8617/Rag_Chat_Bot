import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.api.schemas import AskRequest, AskResponse, UploadResponse
from app.retrieval.embeddings import EmbeddingService
from app.services.qa_service import QAService
from app.services.ingestion_service import IngestionService


logger = logging.getLogger(__name__)

router = APIRouter()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:

    return EmbeddingService()


@lru_cache(maxsize=1)
def get_qa_service() -> QAService:
    return QAService(embedding_service=get_embedding_service())


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(embedding_service=get_embedding_service())


@router.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@router.post("/documents", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):

    try:
        ingestion_service = get_ingestion_service()
    except Exception as e:
        logger.exception("Ingestion service unavailable: %s", e)
        raise HTTPException(
            status_code=503,
            detail=(
                "Document ingestion is not available right now. "
                "Check server configuration (e.g. the embedding "
                "model must be downloaded/cached first)."
            )
        )

    try:
        file_bytes = file.file.read()

        result = ingestion_service.ingest_upload(
            filename=file.filename,
            file_bytes=file_bytes
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        logger.exception(
            "Failed to process /documents upload: %s", e
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process the uploaded document."
        )

@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    try:
        qa_service = get_qa_service()
    except Exception as e:
        logger.exception("QA service unavailable: %s", e)
        raise HTTPException(
            status_code=503,
            detail=(
                "The question-answering service is not available "
                "right now. Check server configuration (e.g. "
                "GEMINI_API_KEY must be set and the embedding "
                "model must be downloaded/cached)."
            )
        )

    try:
        result = qa_service.ask(request.question)

        return result

    except Exception as e:
        logger.exception("Failed to process /ask request: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question."
        )