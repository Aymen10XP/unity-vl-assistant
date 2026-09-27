"""Manual payload-format probe for the legacy LM Studio vision prototype.

This file is intentionally not an automated pytest test because it requires a
running external local-model server. V1's retrieval tutor does not depend on it.
"""

import base64
import io

import requests
from PIL import Image, ImageDraw


URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen2.5-vl-7b"


def main() -> None:
    """Send a synthetic image using several legacy payload shapes for diagnosis."""

    # A generated red circle makes the expected vision response obvious without
    # reading a screenshot or other user data from disk.
    image = Image.new("RGB", (200, 200), "white")
    drawing = ImageDraw.Draw(image)
    drawing.ellipse((50, 50, 150, 150), fill="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii").strip()

    # These formats document which OpenAI-compatible image payload a particular
    # local-server version accepts. Format B is the standards-compatible choice.
    formats = [
        ("A: raw base64 in url", {
            "type": "image_url",
            "image_url": {"url": encoded},
        }),
        ("B: data URL in url", {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encoded}"},
        }),
        ("C: image type with base64 field", {
            "type": "image",
            "image": {"data": encoded, "mime_type": "image/png"},
        }),
    ]

    for name, image_part in formats:
        payload = {
            "model": MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in one short sentence."},
                    image_part,
                ],
            }],
            "max_tokens": 40,
            "temperature": 0.0,
        }
        try:
            response = requests.post(URL, json=payload, timeout=60)
            print(f"\n=== {name} ===")
            print("status:", response.status_code)
            print("body:", response.text[:400])
        except Exception as error:
            print(f"\n=== {name} === EXCEPTION: {error}")


if __name__ == "__main__":
    main()
