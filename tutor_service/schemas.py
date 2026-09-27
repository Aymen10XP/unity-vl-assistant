"""Pydantic contracts shared conceptually by Python and the Unity client."""

from typing import Literal

from pydantic import BaseModel, Field


class UnityContext(BaseModel):
    """Small structured snapshot collected by the Unity Editor plugin."""

    unity_version: str = "unknown"
    project_dimension: Literal["2D", "3D", "unknown"] = "unknown"
    render_pipeline: str = "unknown"
    active_scene: str = ""
    selected_object: str = ""
    selected_components: list[str] = Field(default_factory=list)
    installed_packages: list[str] = Field(default_factory=list)
    is_playing: bool = False


class AskRequest(BaseModel):
    """Question and Editor context sent from the Unity package to Python."""

    question: str = Field(min_length=3, max_length=1000)
    context: UnityContext = Field(default_factory=UnityContext)


class Alternative(BaseModel):
    """One possible lesson shown when the question is ambiguous."""

    lesson_id: str
    title: str
    score: float


class AskResponse(BaseModel):
    """Complete grounded lesson response rendered by the Unity Editor window."""

    request_id: str
    lesson_id: str
    title: str
    summary: str
    steps: list[str]
    verification: list[str]
    common_mistakes: list[str]
    context_notes: list[str]
    confidence: float
    needs_clarification: bool
    clarification: str = ""
    alternatives: list[Alternative] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """Learner rating stored locally for evaluation and future improvement."""

    request_id: str
    lesson_id: str
    question: str
    useful: bool
    comment: str = Field(default="", max_length=1000)
