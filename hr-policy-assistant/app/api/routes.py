import logging

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.api.schemas import AskRequest, AskResponse, UploadResponse
from app.services.qa_service import QAService
from app.services.ingestion_service import IngestionService


logger = logging.getLogger(__name__)

router = APIRouter()

qa_service = QAService()
ingestion_service = IngestionService()


@router.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@router.post("/documents", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):

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
        result = qa_service.ask(request.question)

        return result

    except Exception as e:
        logger.exception("Failed to process /ask request: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question."
        )