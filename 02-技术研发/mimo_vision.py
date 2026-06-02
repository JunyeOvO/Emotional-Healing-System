"""
MIMO Vision LLM client — callable by Claude Code for visual analysis tasks.
Usage: python mimo_vision.py <image_path> [prompt]
Requires MIMO_API_KEY in env or ~/.claude/settings.json.
Uses requests library with proxy support for Clash Verge.
"""
import sys
import os
import base64
import json

PROXY = "http://172.24.48.1:7897"

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def mime_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "webp": "image/webp", "gif": "image/gif"}.get(ext, "image/png")

def call_mimo(image_path: str, prompt: str, max_tokens: int = 2048) -> str:
    import requests

    api_key = os.environ.get("MIMO_API_KEY", "")
    if not api_key:
        settings_path = os.path.expanduser("~/.claude/settings.json")
        try:
            with open(settings_path) as f:
                s = json.load(f)
            api_key = s.get("env", {}).get("MIMO_API_KEY", "")
        except:
            pass
    if not api_key:
        return "[ERROR] MIMO_API_KEY not found"

    base_url = os.environ.get("MIMO_API_BASE", "https://api.xiaomimimo.com/v1")
    model = os.environ.get("MIMO_MODEL", "mimo-v2.5")

    b64 = encode_image(image_path)
    mime = mime_type(image_path)

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        "max_tokens": max_tokens,
    }

    proxies = {"http": PROXY, "https": PROXY}

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            proxies=proxies,
            timeout=120,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[MIMO ERROR] {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mimo_vision.py <image_path> [prompt]")
        sys.exit(1)

    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Describe this image in detail."

    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        sys.exit(1)

    result = call_mimo(image_path, prompt)
    print(result)
