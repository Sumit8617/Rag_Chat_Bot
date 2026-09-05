from fastapi import APIRouter, HTTPException

from app.api.schemas import AskRequest, AskResponse
from app.services.qa_service import QAService


router = APIRouter()

qa_service = QAService()


@router.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    try:
        result = qa_service.ask(request.question)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question."
        )