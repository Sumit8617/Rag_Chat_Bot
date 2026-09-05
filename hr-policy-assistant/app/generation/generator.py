import json
import time

from google import genai

from app.config import settings
from app.models.schemas import AnswerResponse
from app.generation.prompt import build_prompt


class PolicyGenerator:

    def __init__(self):

        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        # Number of retries for temporary API errors.
        self.max_retries = 2

        # Delay between retries.
        self.retry_delay = 2


    def generate(
        self,
        query: str,
        chunks: list[dict]
    ) -> AnswerResponse:

        # -------------------------------------------------
        # Validate chunks
        # -------------------------------------------------

        if not chunks:

            return AnswerResponse(
                answer=(
                    "I could not find this information "
                    "in the uploaded policies."
                ),
                citations=[]
            )


        # -------------------------------------------------
        # Build prompt
        # -------------------------------------------------

        prompt = build_prompt(
            query,
            chunks
        )


        # -------------------------------------------------
        # Generate response with retry
        # -------------------------------------------------

        response = None

        for attempt in range(self.max_retries + 1):

            try:

                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt
                )

                break

            except Exception as exc:

                error_message = str(exc)

                print(
                    f"Gemini API error "
                    f"(attempt {attempt + 1}/"
                    f"{self.max_retries + 1}): "
                    f"{error_message}"
                )

                # -----------------------------------------
                # Detect temporary errors
                # -----------------------------------------

                is_retryable = (
                    "429" in error_message
                    or "503" in error_message
                    or "RESOURCE_EXHAUSTED" in error_message
                    or "UNAVAILABLE" in error_message
                )

                # -----------------------------------------
                # If not retryable, stop immediately
                # -----------------------------------------

                if not is_retryable:

                    return self._error_response(
                        "The AI service encountered an error. "
                        "Please try again later."
                    )

                # -----------------------------------------
                # No more retries
                # -----------------------------------------

                if attempt >= self.max_retries:

                    if "429" in error_message:
                        return self._error_response(
                            "The AI service has reached its "
                            "current request limit. "
                            "Please try again later."
                        )

                    return self._error_response(
                        "The AI service is temporarily "
                        "unavailable. Please try again later."
                    )

                # -----------------------------------------
                # Exponential backoff
                # -----------------------------------------

                delay = self.retry_delay * (2 ** attempt)

                print(
                    f"Retrying Gemini request in "
                    f"{delay} seconds..."
                )

                time.sleep(delay)


        # -------------------------------------------------
        # Validate response
        # -------------------------------------------------

        if response is None:

            return self._error_response(
                "I’m unable to generate an answer right now. "
                "Please try again later."
            )


        # -------------------------------------------------
        # Get response text safely
        # -------------------------------------------------

        try:

            text = response.text

        except Exception:

            text = None


        if not text or not text.strip():

            return self._error_response(
                "The AI service returned an empty response. "
                "Please try again."
            )


        text = text.strip()


        # -------------------------------------------------
        # Remove markdown JSON code fences
        # -------------------------------------------------

        if text.startswith("```json"):

            text = text[7:]

        elif text.startswith("```"):

            text = text[3:]


        if text.endswith("```"):

            text = text[:-3]


        text = text.strip()


        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------

        try:

            data = json.loads(text)

        except json.JSONDecodeError as exc:

            print(
                "Invalid Gemini JSON response:"
            )

            print(text)

            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc


        # -------------------------------------------------
        # Validate Pydantic response
        # -------------------------------------------------

        try:

            return AnswerResponse.model_validate(
                data
            )

        except Exception as exc:

            print(
                "Gemini response does not match "
                "AnswerResponse schema:"
            )

            print(data)

            raise ValueError(
                "Gemini returned an invalid answer structure."
            ) from exc


    # =====================================================
    # Helper for API errors
    # =====================================================

    def _error_response(
        self,
        message: str
    ) -> AnswerResponse:

        return AnswerResponse(
            answer=message,
            citations=[]
        )