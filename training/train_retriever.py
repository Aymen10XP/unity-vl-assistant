"""Fine-tune MiniLM to match beginner questions with the correct Unity lesson.

This is the project's custom deep-learning training step. Multiple-negatives
ranking loss treats every other lesson in a batch as a negative example and
uses backpropagation to improve the transformer's semantic vector space.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

import numpy as np
from torch.utils.data import DataLoader
from sentence_transformers import InputExample, SentenceTransformer
from sentence_transformers.sentence_transformer import losses


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tutor_service.config import BASE_MODEL_NAME, FINE_TUNED_MODEL_PATH, LESSONS_PATH  # noqa: E402
from tutor_service.knowledge import Lesson, load_lessons  # noqa: E402


def split_examples(lessons: list[Lesson], seed: int) -> tuple[list[InputExample], list[tuple[str, int]]]:
    """Hold out one paraphrase per lesson to prevent exact-query leakage."""
    rng = random.Random(seed)
    train: list[InputExample] = []
    validation: list[tuple[str, int]] = []
    for lesson_index, lesson in enumerate(lessons):
        questions = list(lesson.example_questions)
        rng.shuffle(questions)
        validation.append((questions[0], lesson_index))
        for question in questions[1:]:
            train.append(InputExample(texts=[question, lesson.retrieval_text]))
    rng.shuffle(train)
    return train, validation


def recall_metrics(
    model: SentenceTransformer,
    lessons: list[Lesson],
    validation: list[tuple[str, int]],
) -> dict[str, float]:
    """Measure where each correct lesson appears in the semantic ranking."""

    # Encode every lesson and held-out question using the same normalized vector
    # space used by the production retriever.
    lesson_vectors = model.encode(
        [lesson.retrieval_text for lesson in lessons], normalize_embeddings=True
    )
    queries = model.encode([item[0] for item in validation], normalize_embeddings=True)
    similarities = np.asarray(queries) @ np.asarray(lesson_vectors).T
    rankings = np.argsort(similarities, axis=1)[:, ::-1]
    reciprocal_ranks: list[float] = []
    recall_1 = 0
    recall_3 = 0
    for row, (_, expected) in zip(rankings, validation):
        rank = int(np.where(row == expected)[0][0]) + 1
        reciprocal_ranks.append(1.0 / rank)
        recall_1 += int(rank <= 1)
        recall_3 += int(rank <= 3)
    count = len(validation)
    return {
        "recall_at_1": recall_1 / count,
        "recall_at_3": recall_3 / count,
        "mean_reciprocal_rank": float(np.mean(reciprocal_ranks)),
        "validation_questions": count,
    }


def main() -> None:
    """Run reproducible baseline evaluation, fine-tuning, and final evaluation."""

    # Command-line arguments make experiments repeatable in the project report.
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=FINE_TUNED_MODEL_PATH)
    args = parser.parse_args()

    # First establish the pretrained baseline on exactly the same validation set
    # that will be used after training.
    lessons = load_lessons(LESSONS_PATH)
    train_examples, validation = split_examples(lessons, args.seed)
    model = SentenceTransformer(BASE_MODEL_NAME)
    baseline = recall_metrics(model, lessons, validation)

    # Multiple-negatives loss makes the matching lesson positive and treats the
    # other lessons in each batch as negative examples.
    loader = DataLoader(train_examples, shuffle=True, batch_size=args.batch_size)
    loss = losses.MultipleNegativesRankingLoss(model)
    warmup_steps = max(1, int(len(loader) * args.epochs * 0.1))
    model.fit(
        train_objectives=[(loader, loss)],
        epochs=args.epochs,
        warmup_steps=warmup_steps,
        output_path=str(args.output),
        show_progress_bar=True,
    )

    # Save both the reusable model and before/after metrics for honest evaluation.
    trained = recall_metrics(model, lessons, validation)
    report = {
        "base_model": BASE_MODEL_NAME,
        "epochs": args.epochs,
        "training_pairs": len(train_examples),
        "baseline": baseline,
        "fine_tuned": trained,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "training_metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
