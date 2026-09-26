import mss
import base64
import io
import threading
import time
import requests
from PIL import Image
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

from adviceOverlay import AdviceOverlay

# ---------------- Configuration ----------------
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "qwen2.5-vl-3b-instruct"
MONITOR_INDEX = 1   # 1 = primary, 0 = all monitors combined
MAX_IMAGE_SIZE = 1024
JPEG_QUALITY = 80


def capture_frame():
    with mss.MSS() as sct:
        monitor = sct.monitors[MONITOR_INDEX]
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img


def frame_to_base64(img, max_size=MAX_IMAGE_SIZE, quality=JPEG_QUALITY):
    w, h = img.size
    scale = max_size / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def frames_differ(img1, img2, threshold=0.98):
    arr1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2GRAY)
    arr2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2GRAY)
    score, _ = ssim(arr1, arr2, full=True)
    return score < threshold


def analyze_frame(img):
    b64 = frame_to_base64(img)

    prompt = """You are a Unity beginner assistant. Look at this Unity Editor screenshot.

In 2-3 sentences max, tell the user:
1. What they are most likely trying to do right now
2. One specific tip or next step

Be concise. Use simple language. Mention Unity panel names explicitly."""

    payload = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"
                }}
            ]
        }],
        "max_tokens": 150,
        "temperature": 0.3
    }

    response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
    if not response.ok:
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def main():
    overlay = AdviceOverlay()
    overlay.update("Monitoring screen...\nWaiting for activity.")

    last_frame = None
    print("Monitoring screen... (Ctrl+C to stop)")

    def loop():
        nonlocal last_frame
        try:
            current_frame = capture_frame()
        except Exception as e:
            print(f"Capture error: {e}")
            overlay.root.after(2000, loop)
            return

        if last_frame is None or frames_differ(last_frame, current_frame):
            print("\n--- Screen change detected, analyzing... ---")
            overlay.update("Analyzing screen...")
            last_frame = current_frame

            def worker(frame):
                try:
                    advice = analyze_frame(frame)
                    print(f"ADVICE: {advice}")
                    overlay.root.after(0, lambda a=advice: overlay.update(a))
                except Exception as e:
                    err = str(e)
                    print(f"Error: {err}")
                    overlay.root.after(0, lambda m=err: overlay.update(f"Error: {m}"))

            threading.Thread(target=worker, args=(current_frame,), daemon=True).start()

        overlay.root.after(2000, loop)

    overlay.root.after(500, loop)
    overlay.run()


if __name__ == "__main__":
    main()