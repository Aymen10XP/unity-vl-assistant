# README.md

```markdown
# Unity VL Assistant

A real-time AI assistant that watches your Unity Editor and gives contextual tips and guidance as you work. Built for beginners learning Unity development.

The assistant captures your screen, detects meaningful changes in the Unity Editor, sends the frame to a locally-running Vision-Language Model (Qwen2.5-VL), and displays helpful advice in a floating overlay window.

---

## Features

- **Real-time screen monitoring** — Watches the Unity Editor window continuously
- **Change detection** — Only triggers analysis when the screen meaningfully changes (saves compute)
- **Offline inference** — Runs entirely on your machine via LM Studio (no API costs, no internet needed)
- **Contextual advice** — Infers what you're trying to do and suggests next steps
- **Floating overlay** — Displays tips in an always-on-top window beside Unity

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **GPU** | NVIDIA with 4GB VRAM | NVIDIA with 8GB+ VRAM |
| **RAM** | 16GB | 24GB+ |
| **Storage** | 10GB free | 20GB+ free |

> **Note:** This project is optimized for **low-VRAM setups**. It uses the **Qwen2.5-VL-3B** model at 4-bit quantization, which fits in ~3GB VRAM. The 7B model requires 6GB+ VRAM and is not supported on 4GB cards.

---

## Software Requirements

| Software | Version | Purpose |
|---|---|---|
| **Python** | 3.10 or 3.11 | Core orchestration code (avoid 3.12+) |
| **LM Studio** | Latest | Local VLM inference server |
| **NVIDIA Drivers** | Recent | GPU acceleration |
| **VSCode** | Latest | Code editing (optional but recommended) |
| **Unity Editor** | 2021 LTS or newer | The target application |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Aymen10XP/unity-vl-assistant.git
cd unity-vl-assistant
```

### 2. Set up Python environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install and configure LM Studio

1. Download **LM Studio** from [lmstudio.ai](https://lmstudio.ai)
2. In LM Studio, search for **`Qwen2.5-VL-3B-Instruct-GGUF`**
3. Download the **Q4_K_M** quantization (~2-3GB)
4. Load the model — monitor VRAM usage in the bottom bar
   - If VRAM is maxed out, reduce **GPU Layers** in the model settings
   - Overflow layers will use system RAM automatically
5. Go to the **Local Server** tab and click **Start Server**
   - Default port: `1234`
   - Enable **OpenAI-compatible API**

### 4. Configure the project

Copy the example config and adjust as needed:

```bash
cp .env.example .env
```

Edit `.env`:

```env
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
MODEL_NAME=qwen2.5-vl-3b-instruct
CAPTURE_TOP=100
CAPTURE_LEFT=200
CAPTURE_WIDTH=1280
CAPTURE_HEIGHT=720
CHANGE_THRESHOLD=0.98
POLL_INTERVAL=2
```

**Adjust `CAPTURE_*` values to match your Unity Editor window position.** You can use a screenshot tool to find the coordinates.

---

## Usage

### 1. Start LM Studio server

Make sure the model is loaded and the local server is running on port `1234`.

### 2. Launch the assistant

```bash
python src/main.py
```

You should see:
```
Monitoring Unity Editor... (Ctrl+C to stop)
```

### 3. Open Unity and start working

The overlay window will appear. When you make a meaningful change in Unity, the assistant will analyze the screen and display advice.

### 4. Stop

Press `Ctrl+C` in the terminal.

---

## Project Structure

```
unity-vl-assistant/
├── src/
│   ├── main.py              # Entry point — runs the capture loop
│   ├── capture.py           # Screen capture logic (mss)
│   ├── change_detect.py     # Frame comparison (SSIM)
│   ├── vlm_client.py        # LM Studio API client
│   ├── overlay.py           # Floating advice window (tkinter)
│   └── config.py            # Loads .env configuration
├── data/
│   ├── samples/             # Sample screenshots for testing
│   └── annotations/         # (Future) labeled training data
├── notebooks/
│   └── explore.ipynb        # Testing and experimentation
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LM_STUDIO_URL` | `http://localhost:1234/v1/chat/completions` | Local VLM endpoint |
| `MODEL_NAME` | `qwen2.5-vl-3b-instruct` | Model identifier in LM Studio |
| `CAPTURE_TOP` | `100` | Top Y coordinate of Unity window |
| `CAPTURE_LEFT` | `200` | Left X coordinate of Unity window |
| `CAPTURE_WIDTH` | `1280` | Width of capture region |
| `CAPTURE_HEIGHT` | `720` | Height of capture region |
| `CHANGE_THRESHOLD` | `0.98` | SSIM threshold — lower = more sensitive |
| `POLL_INTERVAL` | `2` | Seconds between screen checks |

---

## How It Works

```
┌─────────────────┐
│  Unity Editor   │
└────────┬────────┘
         │ (screen capture every N seconds)
         ▼
┌─────────────────┐
│ Change Detector │  ← SSIM comparison
└────────┬────────┘
         │ (only if changed)
         ▼
┌─────────────────┐
│  VLM Client     │  ← HTTP request to LM Studio
└────────┬────────┘
         │ (advice text)
         ▼
┌─────────────────┐
│ Overlay Window  │
└─────────────────┘
```

1. **Capture** — `mss` grabs the Unity Editor window region
2. **Change detection** — SSIM compares the current frame to the last analyzed frame
3. **Inference** — If changed, the frame is base64-encoded and sent to the local VLM
4. **Display** — The model's response appears in a floating overlay

---

## Troubleshooting

### "Connection refused" when calling LM Studio
- Make sure the LM Studio local server is running (green indicator in the Server tab)
- Verify the port matches `LM_STUDIO_URL` in `.env`

### Model is very slow (5+ seconds per inference)
- Reduce `CAPTURE_WIDTH` and `CAPTURE_HEIGHT` — smaller images process faster
- Increase `POLL_INTERVAL` to reduce query frequency
- In LM Studio, reduce GPU layers and let more layers use CPU (paradoxically faster if VRAM is saturated)

### Out of VRAM errors
- Confirm you downloaded the **Q4_K_M** quantization, not Q8 or FP16
- Reduce GPU layers in LM Studio settings
- Close other GPU-heavy apps (browsers, games)

### Overlay window doesn't stay on top
- On Windows: right-click the window → "Always on top"
- On macOS: the `-topmost` attribute works, but some window managers override it

### Advice is generic or unhelpful
- This is expected with the 3B model on complex scenes
- Try cropping `CAPTURE_*` to focus on the Inspector panel or Scene view specifically
- Improve the prompt in `vlm_client.py` — see the prompt engineering section below

---

## Prompt Engineering

The quality of advice depends heavily on the prompt. Current prompt in `vlm_client.py`:

```python
PROMPT = """You are a Unity beginner assistant. Look at this Unity Editor screenshot.

In 2-3 sentences max, tell the user:
1. What they are most likely trying to do right now
2. One specific tip or next step

Be concise. Use simple language. Mention Unity panel names explicitly."""
```

**Tips for improving:**
- Add context about the user's skill level ("complete beginner")
- Specify what to do if the user is stuck vs. on track
- Constrain output length and forbid jargon
- Include Unity version if behavior differs

---

## Roadmap

- [x] Phase 1: Minimum viable prototype (capture → VLM → overlay)
- [ ] Phase 2: Data collection from Unity tutorials
- [ ] Phase 3: Fine-tune Qwen2.5-VL on annotated editor screenshots
- [ ] Phase 4: Prompt engineering and evaluation
- [ ] Phase 5: Production overlay UI with history and settings
- [ ] Phase 6: Unity Editor plugin for direct action logging (C#)

---

## Contributing

This is a learning project. Contributions welcome — especially:
- Better prompts that produce more useful advice
- Alternative change detection methods
- Support for other VLM backends (llama.cpp, Ollama, etc.)

---

## License

MIT License — see `LICENSE` for details.

---

## Acknowledgments

- [Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct) — the vision-language model
- [LM Studio](https://lmstudio.ai) — local inference runtime
- [mss](https://python-mss.readthedocs.io/) — fast cross-platform screen capture
```

---

## Suggested `requirements.txt`

```txt
mss>=9.0.1
Pillow>=10.0.0
numpy>=1.24.0
opencv-python>=4.8.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## Suggested `.env.example`

```env
# LM Studio configuration
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
MODEL_NAME=qwen2.5-vl-3b-instruct

# Screen capture region (adjust to your Unity window)
CAPTURE_TOP=100
CAPTURE_LEFT=200
CAPTURE_WIDTH=1280
CAPTURE_HEIGHT=720

# Change detection (SSIM threshold, 0-1, lower = more sensitive)
CHANGE_THRESHOLD=0.98

# How often to check the screen (seconds)
POLL_INTERVAL=2
```

## Suggested `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/

# Environment
.env

# Data
data/samples/*.jpg
data/samples/*.png
!data/samples/.gitkeep

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```