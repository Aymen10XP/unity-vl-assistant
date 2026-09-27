"""Loading and validation for the human-editable Unity lesson library."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Lesson:
    """Typed representation of one reviewed lesson from the JSON knowledge base."""

    id: str
    title: str
    summary: str
    difficulty: str
    dimensions: list[str]
    tags: list[str]
    component_hints: list[str]
    package_hints: list[str]
    example_questions: list[str]
    prerequisites: list[str]
    steps: list[str]
    verification: list[str]
    common_mistakes: list[str]

    @property
    def retrieval_text(self) -> str:
        """Text embedded once and cached by the neural retriever."""
        parts = [
            self.title,
            self.summary,
            " ".join(self.tags),
            " ".join(self.example_questions),
            " ".join(self.prerequisites),
        ]
        return "\n".join(parts)


def load_lessons(path: Path) -> list[Lesson]:
    """Read lesson JSON, convert records to typed objects, and reject duplicate IDs."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    lessons = [Lesson(**item) for item in raw]
    ids = [lesson.id for lesson in lessons]
    if len(ids) != len(set(ids)):
        raise ValueError("Lesson IDs must be unique")
    if not lessons:
        raise ValueError("At least one lesson is required")
    return lessons
