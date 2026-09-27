# Unity Beginner Assistant — V1

A context-aware Unity tutor that retrieves verified, step-by-step lessons with a
compact neural semantic model. It runs locally, does not require Qwen or a
continuous screenshot feed, and uses current Unity Editor context to improve
guidance.

## Architecture

- **Unity Editor package** — dockable question-and-guidance window.
- **Python FastAPI service** — localhost API on `127.0.0.1:8765`.
- **MiniLM semantic retriever** — matches natural-language questions to lessons.
- **Structured lesson library** — editable facts, steps, checks, and mistakes.
- **Feedback log** — local usefulness signals for evaluation and future training.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

In Unity, open **Window → Package Manager**, choose **Add package from disk**,
and select `unity_package/UnityBeginnerAssistant/package.json`. Then open
**Window → Unity Beginner Assistant**.

The first question downloads the small base MiniLM model if no locally
fine-tuned checkpoint exists. To fine-tune the custom retriever:

```powershell
.\.venv\Scripts\python.exe training\train_retriever.py
```

Restart the API afterward; it automatically prefers the checkpoint under
`models/unity-tutor-minilm`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The original screenshot prototype remains in `capture_loop.py` for comparison,
but it is not part of the V1 tutor architecture.
