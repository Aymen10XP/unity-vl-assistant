# test_vision.py
import base64, io, requests, json
from PIL import Image, ImageDraw

URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen2.5-vl-3b-instruct"

# Make a tiny, obvious test image: red circle on white background
img = Image.new("RGB", (200, 200), "white")
d = ImageDraw.Draw(img)
d.ellipse((50, 50, 150, 150), fill="red")
buf = io.BytesIO()
img.save(buf, format="PNG")
b64 = base64.b64encode(buf.getvalue()).decode("ascii").strip()

print("b64 length:", len(b64))
print("b64 starts with:", b64[:20])

# Try every plausible payload format, one at a time
formats = [
    ("A: raw base64 in url", {
        "type": "image_url",
        "image_url": {"url": b64}
    }),
    ("B: data URL in url", {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"}
    }),
    ("C: image type w/ base64 field", {
        "type": "image",
        "image": {"data": b64, "mime_type": "image/png"}
    }),
]

for name, img_part in formats:
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one short sentence."},
                img_part
            ]
        }],
        "max_tokens": 40,
        "temperature": 0.0
    }
    try:
        r = requests.post(URL, json=payload, timeout=60)
        print(f"\n=== {name} ===")
        print("status:", r.status_code)
        print("body:", r.text[:400])
    except Exception as e:
        print(f"\n=== {name} === EXCEPTION: {e}")