from pydantic import BaseModel, Field
from app.models.schemas import Citation, AnswerResponse


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question about HR policies"
    )


# AskResponse is canonical AnswerResponse model
AskResponse = AnswerResponse


class UploadResponse(BaseModel):
    document: str
    chunks_indexed: int