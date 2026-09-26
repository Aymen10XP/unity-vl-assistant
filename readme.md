```markdown
# Unity VL Assistant

A real-time AI assistant that watches your Unity Editor and gives contextual tips and guidance as you work. Built for beginners learning Unity development.

The assistant captures your screen, detects meaningful changes, sends the frame to a locally-running Vision-Language Model (Qwen2.5-VL), and displays helpful advice in a floating overlay window — all offline.

---

## Features

- **Real-time screen monitoring** — Watches the primary monitor continuously
- **Change detection** — Only triggers analysis when the screen meaningfully changes (saves compute)
- **Offline inference** — Runs entirely on your machine via LM Studio (no API costs, no internet needed)
- **Contextual advice** — Infers what you're trying to do and suggests next steps
- **Non-blocking overlay** — Floating always-on-top window; inference runs on a worker thread so the UI never freezes
- **JPEG pipeline** — Frames are resized and encoded as JPEG to keep payloads small and inference fast

---

## Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **GPU** | NVIDIA with 4GB VRAM | NVIDIA with 8GB+ VRAM |
| **RAM** | 16GB | 24GB+ |
| **Storage** | 10GB free | 20GB+ free |

> **Note:** Optimized for **low-VRAM setups**. Uses **Qwen2.5-VL-3B** at 4-bit quantization (~3GB VRAM). The 7B model needs 6GB+ VRAM and is not supported on 4GB cards.

---

## Software Requirements

| Software | Version | Purpose |
|---|---|---|
| **Python** | 3.10 or 3.11 | Core orchestration (avoid 3.12+) |
| **LM Studio** | Latest | Local VLM inference server |
| **NVIDIA Drivers** | Recent | GPU acceleration |
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
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Install and configure LM Studio

1. Download **LM Studio** from [lmstudio.ai](https://lmstudio.ai)
2. In the **Search** tab, search for **`Qwen2.5-VL-3B-Instruct GGUF`**
3. Pick the **`lmstudio-community`** result and download the **Q4_K_M** quantization (~2–3GB)

   > ⚠️ **Critical:** The model bundle must include an **`mmproj-model-f16.gguf`** file. This is the vision adapter — without it, the model loads as text-only and every image request fails with a confusing 400 error from LM Studio.

4. Load the model in the **Chat** tab. Look for a **vision / eye icon** next to the model name in the top bar. If it's missing, the mmproj wasn't downloaded — delete the model and re-download from `lmstudio-community`.

5. Go to the **Local Server** tab and click **Start Server**
   - Default port: `1234`
   - Base URL should read: `http://localhost:1234/v1`

### 4. Configure the project

```bash
cp .env.example .env
```

Edit `.env`:

```env
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
MODEL_NAME=qwen2.5-vl-3b-instruct
MONITOR_INDEX=1
MAX_IMAGE_SIZE=1024
JPEG_QUALITY=80
CHANGE_THRESHOLD=0.98
POLL_INTERVAL=2
```

`MONITOR_INDEX` picks which display to capture: `1` = primary monitor, `0` = all monitors combined.

---

## Usage

### 1. Start LM Studio server

Make sure the Qwen2.5-VL model is loaded **with its vision adapter** and the server is running on port `1234`.

### 2. Launch the assistant

```bash
python src/main.py
```

You should see:

```
Monitoring screen... (Ctrl+C to stop)
```

### 3. Open Unity and work

The overlay appears. Whenever the screen meaningfully changes, the assistant analyzes the frame and displays advice.

### 4. Stop

Press `Ctrl+C` in the terminal.

---

## Project Structure

```
unity-vl-assistant/
├── src/
│   ├── main.py              # Entry point — capture loop
│   ├── capture.py           # Screen capture (mss)
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
| `MONITOR_INDEX` | `1` | 1 = primary monitor, 0 = all monitors |
| `MAX_IMAGE_SIZE` | `1024` | Longest side of resized frame (px) |
| `JPEG_QUALITY` | `80` | JPEG compression quality |
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
│  (worker thread)│
└────────┬────────┘
         │ (advice text)
         ▼
┌─────────────────┐
│ Overlay Window  │
└─────────────────┘
```

1. **Capture** — `mss` grabs the primary monitor
2. **Change detection** — SSIM compares the current frame to the last analyzed one
3. **Inference** — If changed, the frame is resized, JPEG-encoded, base64-wrapped in a data URL, and sent to the local VLM on a background thread
4. **Display** — The model's response appears in the floating overlay via `root.after(0, ...)` (tkinter is not thread-safe)

---

## Troubleshooting

### LM Studio returns `400 Bad Request` on image requests

The single most common cause is that the model was loaded **without its vision adapter**. LM Studio will list the model in `/v1/models` even when vision is missing, and the errors it returns are misleading (`Invalid url.` or `'url' field must be a base64 encoded image`).

**Fix:**
1. In LM Studio, delete the model
2. Re-download from **`lmstudio-community/Qwen2.5-VL-3B-Instruct-GGUF`**
3. Confirm `mmproj-model-f16.gguf` is present in the same folder as the main `.gguf`
4. Load the model and verify the **vision icon** appears next to its name
5. Restart the local server

The correct payload format (confirmed working) is:

```json
{
  "type": "image_url",
  "image_url": { "url": "data:image/jpeg;base64,<BASE64_STRING>" }
}
```

### "Connection refused" when calling LM Studio

- Ensure the LM Studio local server is running (green indicator in the Server tab)
- Verify the port matches `LM_STUDIO_URL` in `.env`

### Model is very slow (5+ seconds per inference)

- Reduce `MAX_IMAGE_SIZE` (e.g. 768) — smaller images process faster
- Increase `POLL_INTERVAL` to reduce query frequency
- In LM Studio, reduce GPU layers and let more layers use CPU (paradoxically faster if VRAM is saturated)

### Out of VRAM errors

- Confirm you downloaded the **Q4_K_M** quantization, not Q8 or FP16
- Reduce GPU layers in LM Studio settings
- Close other GPU-heavy apps (browsers, games)

### Overlay window doesn't stay on top

- On Windows: right-click the window → "Always on top"
- On macOS: `-topmost` works but some window managers override it

### Advice is generic or unhelpful

- Expected with the 3B model on complex scenes
- Try `MAX_IMAGE_SIZE=1280` or `1536` for better text legibility (Unity panel labels)
- Improve the prompt in `vlm_client.py` — see Prompt Engineering below

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

## Roadmap

- [x] **Phase 1:** Minimum viable prototype (capture → VLM → overlay)
- [ ] **Phase 2:** Data collection from Unity tutorials
- [ ] **Phase 3:** Fine-tune Qwen2.5-VL on annotated editor screenshots
- [ ] **Phase 4:** Prompt engineering and evaluation
- [ ] **Phase 5:** Production overlay UI with history and settings
- [ ] **Phase 6:** Unity Editor plugin for direct action logging (C#)

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

## Companion files

### `requirements.txt`

```txt
mss>=9.0.1
Pillow>=10.0.0
numpy>=1.24.0
opencv-python>=4.8.0
scikit-image>=0.22.0
requests>=2.31.0
python-dotenv>=1.0.0
```

### `.env.example`

```env
# LM Studio configuration
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
MODEL_NAME=qwen2.5-vl-3b-instruct

# Screen capture
MONITOR_INDEX=1
MAX_IMAGE_SIZE=1024
JPEG_QUALITY=80

# Change detection (SSIM threshold, 0-1, lower = more sensitive)
CHANGE_THRESHOLD=0.98

# How often to check the screen (seconds)
POLL_INTERVAL=2
```