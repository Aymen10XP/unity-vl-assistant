import numpy as np

from tutor_service.config import LESSONS_PATH
from tutor_service.knowledge import load_lessons
from tutor_service.retriever import LessonRetriever
from tutor_service.schemas import UnityContext


def keyword_encoder(texts: list[str]) -> np.ndarray:
    """Tiny deterministic encoder keeps unit tests offline and fast."""
    keywords = ["camera", "physics", "button", "animation", "prefab", "audio"]
    rows = []
    for text in texts:
        lowered = text.lower()
        row = np.array([lowered.count(word) for word in keywords], dtype=np.float32)
        if not row.any():
            row[-1] = 0.001
        rows.append(row / np.linalg.norm(row))
    return np.stack(rows)


def test_camera_question_retrieves_camera_lesson():
    """Verify that ranking routes a clear camera question to the camera lesson."""

    retriever = LessonRetriever(load_lessons(LESSONS_PATH), keyword_encoder)
    result = retriever.ask(
        "How can the camera follow my player?",
        UnityContext(selected_object="Main Camera", selected_components=["Camera"]),
    )
    assert result.lesson_id == "camera_follow"
    assert result.steps


def test_play_mode_produces_context_warning():
    """Verify that context rules warn beginners about temporary Play Mode edits."""

    retriever = LessonRetriever(load_lessons(LESSONS_PATH), keyword_encoder)
    result = retriever.ask(
        "How do I create a prefab?",
        UnityContext(is_playing=True),
    )
    assert any("Exit Play Mode" in note for note in result.context_notes)
