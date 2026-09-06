from pydantic import BaseModel, Field

from app.models.schemas import Citation


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question about HR policies"
    )


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]


class UploadResponse(BaseModel):
    document: str
    chunks_indexed: int