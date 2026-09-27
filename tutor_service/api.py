"""FastAPI boundary used by the Unity Editor window over localhost only."""

from datetime import datetime, timezone
import json
from threading import Lock

from fastapi import FastAPI

from .config import FEEDBACK_PATH, LESSONS_PATH, MODEL_NAME_OR_PATH
from .knowledge import load_lessons
from .retriever import LessonRetriever, sentence_transformer_encoder
from .schemas import AskRequest, AskResponse, FeedbackRequest


class TutorRuntime:
    """Lazy model container: startup is instant; the first question loads MiniLM."""

    def __init__(self):
        """Load inexpensive JSON immediately but postpone the neural model."""

        self.lessons = load_lessons(LESSONS_PATH)
        self.retriever: LessonRetriever | None = None
        self.lock = Lock()

    def get_retriever(self) -> LessonRetriever:
        """Create the CPU retriever once, safely handling simultaneous first requests."""

        if self.retriever is None:
            with self.lock:
                if self.retriever is None:
                    encoder = sentence_transformer_encoder(MODEL_NAME_OR_PATH)
                    self.retriever = LessonRetriever(self.lessons, encoder)
        return self.retriever


def create_app(runtime: TutorRuntime | None = None) -> FastAPI:
    """Build the web application; injectable runtime keeps unit testing simple."""

    runtime = runtime or TutorRuntime()
    application = FastAPI(title="Unity Beginner Tutor", version="1.0.0")

    @application.get("/health")
    def health() -> dict[str, object]:
        """Report service readiness without forcing the neural model to load."""

        return {
            "status": "ok",
            "lessons": len(runtime.lessons),
            "model_loaded": runtime.retriever is not None,
            "model": MODEL_NAME_OR_PATH,
        }

    @application.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        """Convert one learner question into the highest-ranked grounded lesson."""

        return runtime.get_retriever().ask(request.question, request.context)

    @application.post("/feedback")
    def feedback(request: FeedbackRequest) -> dict[str, str]:
        """Append feedback as JSON Lines so every record is independently readable."""

        FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = request.model_dump()
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        with FEEDBACK_PATH.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"status": "saved"}

    return application


app = create_app()
