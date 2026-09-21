import mss
import base64
import io
import time
import requests
from PIL import Image
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


# Configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "qwen2.5-vl-3b-instruct"

# Screen capture region (adjust to Unity editor window)
# Format: {"top": y, "left": x, "width": w, "height": h}
CAPTURE_REGION = {"top": 100, "left": 200, "width": 1280, "height": 720}

def capture_frame(region):
    with mss.mss() as sct:
        screenshot = sct.grab(region)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

def frame_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def frames_differ(img1, img2, threshold=0.98):
    """Returns True if frames are meaningfully different."""
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
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ],
        "max_tokens": 150,
        "temperature": 0.3
    }

    response = requests.post(LM_STUDIO_URL, json=payload, timeout=30)
    return response.json()["choices"][0]["message"]["content"]

# Main loop
last_frame = None
print("Monitoring Unity Editor... (Ctrl+C to stop)")

while True:
    current_frame = capture_frame(CAPTURE_REGION)
    
    if last_frame is None or frames_differ(last_frame, current_frame):
        print("\n--- Screen change detected, analyzing... ---")
        try:
            advice = analyze_frame(current_frame)
            print(f"ADVICE: {advice}")
        except Exception as e:
            print(f"Error: {e}")
        last_frame = current_frame
    
    time.sleep(2)