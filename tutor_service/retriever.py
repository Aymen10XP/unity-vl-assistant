"""Semantic lesson retrieval powered by a compact transformer.

The model does not generate facts. It embeds a beginner's question and every
curated lesson into the same vector space. Cosine similarity selects the most
relevant lesson; deterministic context rules then adapt the guidance.
"""

from __future__ import annotations

from collections.abc import Callable
import re
from uuid import uuid4

import numpy as np

from .knowledge import Lesson
from .schemas import Alternative, AskResponse, UnityContext


Encoder = Callable[[list[str]], np.ndarray]


def sentence_transformer_encoder(model_name_or_path: str) -> Encoder:
    """Load MiniLM lazily so health checks stay fast and testable."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name_or_path, device="cpu")

    def encode(texts: list[str]) -> np.ndarray:
        """Convert text into normalized float vectors used for cosine similarity."""

        return np.asarray(
            model.encode(texts, normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )

    return encode


class LessonRetriever:
    """Rank lessons semantically, then adapt the winner with transparent rules."""

    def __init__(self, lessons: list[Lesson], encoder: Encoder):
        """Store lessons and precompute their embeddings once for fast questions."""

        self.lessons = lessons
        self.encoder = encoder
        # Lesson vectors never change at runtime, so calculate them only once.
        self.lesson_embeddings = encoder([lesson.retrieval_text for lesson in lessons])

    def ask(self, question: str, context: UnityContext) -> AskResponse:
        """Find the best lesson and package it for the step-by-step Unity UI."""

        # The selected object and project type help distinguish otherwise similar
        # questions such as 2D physics versus 3D physics.
        query = self._contextual_query(question, context)
        query_vector = self.encoder([query])[0]

        # Because all vectors are normalized, a dot product is cosine similarity.
        # Context boosts are intentionally small so semantics remains dominant.
        semantic_scores = self.lesson_embeddings @ query_vector
        scores = semantic_scores + self._context_boosts(question, context)
        ranked = np.argsort(scores)[::-1]

        best_index = int(ranked[0])
        best = self.lessons[best_index]
        best_score = float(scores[best_index])
        second_score = float(scores[int(ranked[1])]) if len(ranked) > 1 else 0.0
        margin = best_score - second_score

        # Low absolute confidence or a small gap between the first two results
        # means the system should ask instead of pretending to be certain.
        # These thresholds should later be calibrated on a larger validation set.
        needs_clarification = best_score < 0.34 or margin < 0.025
        alternatives = [
            Alternative(
                lesson_id=self.lessons[int(i)].id,
                title=self.lessons[int(i)].title,
                score=round(float(scores[int(i)]), 4),
            )
            for i in ranked[:3]
        ]

        return AskResponse(
            request_id=str(uuid4()),
            lesson_id=best.id,
            title=best.title,
            summary=best.summary,
            steps=best.steps,
            verification=best.verification,
            common_mistakes=best.common_mistakes,
            context_notes=self._context_notes(best, context),
            confidence=round(max(0.0, min(1.0, best_score)), 4),
            needs_clarification=needs_clarification,
            clarification=(
                "I found several possible lessons. Which of these best matches your goal?"
                if needs_clarification
                else ""
            ),
            alternatives=alternatives,
        )

    @staticmethod
    def _contextual_query(question: str, context: UnityContext) -> str:
        """Turn the question and safe Unity metadata into one embedding input."""

        components = ", ".join(context.selected_components) or "none"
        return (
            f"Beginner Unity question: {question}\n"
            f"Project: {context.project_dimension}, {context.render_pipeline}.\n"
            f"Selected object: {context.selected_object or 'none'}. "
            f"Components: {components}."
        )

    def _context_boosts(self, question: str, context: UnityContext) -> np.ndarray:
        """Small transparent boosts supplement semantics with exact Unity state."""
        tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
        components = {item.lower() for item in context.selected_components}
        packages = {item.lower() for item in context.installed_packages}
        boosts = np.zeros(len(self.lessons), dtype=np.float32)

        for index, lesson in enumerate(self.lessons):
            tag_hits = len(tokens.intersection(tag.lower() for tag in lesson.tags))
            boosts[index] += min(tag_hits * 0.018, 0.072)
            if context.project_dimension in lesson.dimensions:
                boosts[index] += 0.02
            if components.intersection(hint.lower() for hint in lesson.component_hints):
                boosts[index] += 0.035
            if packages.intersection(hint.lower() for hint in lesson.package_hints):
                boosts[index] += 0.035
        return boosts

    @staticmethod
    def _context_notes(lesson: Lesson, context: UnityContext) -> list[str]:
        """Create deterministic warnings without asking a language model to invent them."""

        notes: list[str] = []
        existing = {item.lower() for item in context.selected_components}
        missing = [item for item in lesson.component_hints if item.lower() not in existing]
        if context.selected_object and missing:
            notes.append(
                f"{context.selected_object} does not currently show: {', '.join(missing)}. "
                "Add only the components required by the steps below."
            )
        if context.project_dimension not in ("unknown", *lesson.dimensions):
            notes.append(
                f"This lesson targets {', '.join(lesson.dimensions)} projects, but this project "
                f"appears to be {context.project_dimension}. Choose the matching alternative."
            )
        if context.is_playing:
            notes.append("Exit Play Mode before making changes you want Unity to save.")
        return notes
