"""Central configuration so paths and model choices are easy to explain/change."""

from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LESSONS_PATH = PROJECT_ROOT / "data" / "beginner_lessons.json"
FEEDBACK_PATH = PROJECT_ROOT / "data" / "feedback.jsonl"

# A fine-tuned model is preferred. Until training is run, the compact generic
# MiniLM checkpoint gives useful semantic retrieval without a GPU.
FINE_TUNED_MODEL_PATH = PROJECT_ROOT / "models" / "unity-tutor-minilm"
BASE_MODEL_NAME = os.getenv(
    "UNITY_TUTOR_BASE_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
MODEL_NAME_OR_PATH = (
    str(FINE_TUNED_MODEL_PATH)
    if FINE_TUNED_MODEL_PATH.exists()
    else BASE_MODEL_NAME
)
