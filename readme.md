# Unity Beginner Assistant

A lightweight, context-aware Unity tutor for beginners. The learner asks a
question inside a dockable Unity Editor window, and a locally running Python
service uses a fine-tuned MiniLM model to retrieve a reviewed, step-by-step
lesson.

V1 does **not** use a generative LLM, a cloud API, or continuous screenshots.
It runs locally and uses the selected GameObject, its components, project type,
render pipeline, installed packages, scene, and Play Mode state to improve
lesson selection.

## What V1 includes

- A Unity Editor package with a dockable tutor window
- Natural-language Unity questions
- 17 structured beginner lessons
- Context-aware semantic lesson retrieval
- One instruction at a time
- Verification checkpoints and common mistakes
- Clarification choices for ambiguous questions
- Local thumbs-up/down feedback
- A reproducible MiniLM fine-tuning pipeline
- Automated Python tests

## How the deep-learning component works

The project fine-tunes `sentence-transformers/all-MiniLM-L6-v2` using PyTorch
and Sentence Transformers. Training uses question–lesson pairs with
`MultipleNegativesRankingLoss`:

1. MiniLM converts a learner question and every lesson into dense vectors.
2. Contrastive training moves matching pairs closer and unrelated pairs apart.
3. At runtime, normalized dot products rank lessons by cosine similarity.
4. Small transparent boosts use relevant Unity context without replacing the
   neural ranking.

The model retrieves facts; it does not invent them. The actual instructions are
stored in `data/beginner_lessons.json`, so lessons can be reviewed and updated
without retraining for every wording change.

On the initial held-out set, fine-tuning improved Recall@1 from **88.24%** to
**94.12%**. The dataset is intentionally small and should be expanded before
treating this as a final scientific result.

## Repository layout

```text
unity-vl-assistant/
├── main.py                         # Starts the local FastAPI service
├── tutor_service/                  # API, schemas, lesson loader, retriever
├── training/train_retriever.py     # Fine-tunes and evaluates MiniLM
├── data/beginner_lessons.json      # Reviewed teaching knowledge
├── tests/                          # Offline automated tests
├── unity_package/
│   └── UnityBeginnerAssistant/     # Package installed into Unity
├── capture_loop.py                 # Legacy screenshot prototype
└── requirements.txt
```

## Requirements

- Windows 10 or 11
- Python 3.10 or 3.11
- Git
- Unity 2021.3 or newer
- Internet access for the first Python dependency/model download

A GPU is not required. MiniLM inference runs on CPU. The first model download
is approximately 90 MB.

## 1. Clone the repository

```powershell
git clone https://github.com/Aymen10XP/unity-vl-assistant.git
cd unity-vl-assistant
```

After V1 is merged, it is available directly from `main`. To inspect the release
branch before or independently of the merge:

```powershell
git switch release/v1-unity-tutor
```

## 2. Create the Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Using the virtual environment's Python explicitly avoids PowerShell activation
policy problems.

## 3. Run the automated tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected result:

```text
3 passed
```

## 4. Train the Unity retriever

Model artifacts are reproducible and intentionally excluded from Git. Each new
clone should run the training command once:

```powershell
.\.venv\Scripts\python.exe training\train_retriever.py --epochs 4
```

This command:

- downloads the compact MiniLM base model if necessary;
- creates training and held-out validation pairs;
- evaluates the generic model;
- fine-tunes it with contrastive learning;
- evaluates the fine-tuned model;
- saves the result under `models/unity-tutor-minilm`;
- writes `training_metrics.json` beside the model.

Training is small enough to run on CPU. Restart the API after retraining so it
loads the new checkpoint.

If training is skipped, the service still works with generic MiniLM, but it
will not use the project-specific fine-tuned weights.

## 5. Start the local tutor service

```powershell
.\.venv\Scripts\python.exe main.py
```

Keep this terminal open while using the Unity assistant. Expected output:

```text
Uvicorn running on http://127.0.0.1:8765
```

Confirm that the service is healthy by opening:

```text
http://127.0.0.1:8765/health
```

The response should contain `"status": "ok"` and `"lessons": 17`.
`model_loaded` is initially false because the model loads lazily on the first
question.

## 6. Install the package in a Unity project

1. Open the target Unity project.
2. Open **Window → Package Manager**.
3. Click the `+` button.
4. Choose **Add package from disk…**.
5. Select:

```text
<cloned-repository>\unity_package\UnityBeginnerAssistant\package.json
```

6. Wait for Unity to compile the Editor assembly.
7. Open **Window → Unity Beginner Assistant**.

Because this is a local package reference, changes made in the cloned package
directory are reflected in the Unity project after **Assets → Refresh**.

## 7. Test the assistant in Unity

1. Make sure `main.py` is still running.
2. Select a relevant object in the Hierarchy.
3. Open **Window → Unity Beginner Assistant**.
4. Enter a question.
5. Click **Guide me**.
6. Use **I completed this step** to progress through the lesson.
7. Expand verification and common mistakes.
8. Submit feedback using **Yes** or **No**.

Recommended test cases:

| Selected object | Question | Expected lesson |
|---|---|---|
| Main Camera | How do I make the camera follow my player? | `camera_follow` |
| Cube with Collider | How do I make this object fall? | `rigidbody_3d` |
| UI Button | How do I run code when this button is clicked? | `ui_button` |
| Player | How do I move my player with the keyboard? | `basic_movement` |
| Any configured object | How do I turn this into a prefab? | `create_prefab` |

The first question can take slightly longer because the model is loaded into
memory at that moment. Later questions should be faster.

## API-only smoke test

With `main.py` running, a colleague can test the trained service without Unity:

```powershell
$body = @{
    question = "How do I make the camera follow my player?"
    context = @{
        unity_version = "6000.0"
        project_dimension = "3D"
        render_pipeline = "UniversalRenderPipelineAsset"
        active_scene = "SampleScene"
        selected_object = "Main Camera"
        selected_components = @("Transform", "Camera", "AudioListener")
        installed_packages = @("com.unity.cinemachine")
        is_playing = $false
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8765/ask" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

The returned `lesson_id` should be `camera_follow`.

## Feedback and local files

Feedback is appended locally to:

```text
data/feedback.jsonl
```

The following directories/files are intentionally ignored by Git:

- `.venv/`
- `models/`
- `docs/`
- `data/feedback.jsonl`
- Python cache/test cache files

## Troubleshooting

### The Unity menu does not appear

- Wait for script compilation to finish.
- Select **Assets → Refresh**.
- Check the Unity Console for C# compiler errors.
- Remove and re-add the package from disk if its local path changed.
- Restart Unity after package changes when necessary.

### Unity says it cannot connect to the tutor API

Start the service from the repository root:

```powershell
.\.venv\Scripts\python.exe main.py
```

Verify `http://127.0.0.1:8765/health`. The Unity client intentionally connects
only to localhost.

### A question retrieves the wrong lesson

- Select the most relevant GameObject before asking.
- Make the goal more specific.
- Choose one of the clarification alternatives.
- Add reviewed question variations to the lesson dataset and retrain.

### The first question is slow

The neural model loads lazily. This is expected only on the first request after
starting the service.

## Reproducing or rolling back the release

The V1 work is preserved through feature and release commits. Useful commands:

```powershell
# Inspect history
git log --oneline --graph --decorate --all

# Create a safety branch before experimenting
git switch -c experiment/my-change

# Return to the V1 release branch
git switch release/v1-unity-tutor
```

Avoid deleting model/data changes blindly. Commit source changes on a separate
branch so they can be reviewed, merged, or reverted safely.

## Current limitations

- The initial knowledge base contains 17 lessons.
- The held-out evaluation set is small.
- Confidence thresholds need calibration with more learner questions.
- V1 does not inspect arbitrary user scripts or diagnose Console errors.
- Lessons need human review when Unity workflows change.

Error diagnosis and a larger curriculum are planned for later versions.
