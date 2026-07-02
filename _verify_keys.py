#!/usr/bin/env python3
"""
Temporary script to verify all API keys used by the project.
Run: python _verify_keys.py
This will be removed after Phase 1 cleanup is complete.
"""
import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def ok(msg=""):
    print(f"  {GREEN}✔{RESET} {msg}" if msg else f"  {GREEN}✔{RESET}")

def fail(msg=""):
    print(f"  {RED}✘{RESET} {msg}" if msg else f"  {RED}✘{RESET}")

def warn(msg=""):
    print(f"  {YELLOW}⚠{RESET} {msg}" if msg else f"  {YELLOW}⚠{RESET}")

results = {"pass": 0, "fail": 0, "warn": 0}

# ─── 1. Gemini ────────────────────────────────────────────────────────
print("\n1. Gemini API Key")
key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if key:
    ok(f"Key found: ...{key[-8:]}")
    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Reply with just the word: OK",
            config={"max_output_tokens": 50},
        )
        text = response.text
        if text and text.strip():
            ok(f"Gemini API reachable — response: {text.strip()[:50]}")
            results["pass"] += 1
        else:
            warn("Gemini API returned empty response (may need higher max_tokens)")
            results["warn"] += 1
    except Exception as e:
        warn(f"Gemini API call failed: {e}")
        results["warn"] += 1
else:
    fail("Missing GEMINI_API_KEY (or GOOGLE_API_KEY)")
    results["fail"] += 1

# ─── 2. Google Cloud credentials ──────────────────────────────────────
print("\n2. Google Cloud (TTS + Secret Manager)")
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if cred_path and os.path.exists(cred_path):
    ok(f"Credentials file exists: {cred_path}")
    results["pass"] += 1
else:
    fail(f"GOOGLE_APPLICATION_CREDENTIALS not set or file not found: {cred_path}")
    results["fail"] += 1

# ─── 3. Azure Speech ──────────────────────────────────────────────────
print("\n3. Azure Speech")
az_key = os.getenv("AZURE_SPEECH_KEY")
az_region = os.getenv("AZURE_SPEECH_REGION")
if az_key and az_region:
    ok(f"Key found: ...{az_key[-4:]}, Region: {az_region}")
    try:
        import azure.cognitiveservices.speech as speechsdk
        speech_config = speechsdk.SpeechConfig(subscription=az_key, region=az_region)
        ok("Azure SDK initialized successfully")
        results["pass"] += 1
    except Exception as e:
        warn(f"Azure SDK init failed: {e}")
        results["warn"] += 1
else:
    warn("AZURE_SPEECH_KEY or AZURE_SPEECH_REGION not set (optional, will fallback)")
    results["warn"] += 1

# ─── 4. Hugging Face ──────────────────────────────────────────────────
print("\n4. Hugging Face Inference API")
hf_key = os.getenv("HUGGINGFACE_API_KEY")
if hf_key:
    ok(f"Key found: ...{hf_key[-8:]}")
    try:
        import requests
        r = requests.get(
            "https://api-inference.huggingface.co/models/facebook/bart-large-mnli",
            headers={"Authorization": f"Bearer {hf_key}"},
            timeout=5
        )
        if r.status_code in (200, 503):
            ok(f"API reachable (HTTP {r.status_code})")
            results["pass"] += 1
        else:
            warn(f"API returned HTTP {r.status_code}")
            results["warn"] += 1
    except Exception as e:
        warn(f"Could not reach Hugging Face API: {e}")
        results["warn"] += 1
else:
    fail("Missing HUGGINGFACE_API_KEY")
    results["fail"] += 1

# ─── 5. Pexels ────────────────────────────────────────────────────────
print("\n5. Pexels API")
pexels_key = os.getenv("PEXELS_API_KEY")
if pexels_key:
    ok(f"Key found: ...{pexels_key[-4:]}")
    try:
        import requests
        r = requests.get(
            "https://api.pexels.com/videos/search?query=nature&per_page=1",
            headers={"Authorization": pexels_key},
            timeout=5
        )
        if r.status_code == 200:
            ok(f"API reachable (HTTP 200)")
            results["pass"] += 1
        else:
            warn(f"Pexels returned HTTP {r.status_code}")
            results["warn"] += 1
    except Exception as e:
        warn(f"Could not reach Pexels API: {e}")
        results["warn"] += 1
else:
    warn("Missing PEXELS_API_KEY (optional, will fallback)")
    results["warn"] += 1

# ─── 6. Pixabay ───────────────────────────────────────────────────────
print("\n6. Pixabay API")
pix_key = os.getenv("PIXABAY_API_KEY")
if pix_key:
    ok(f"Key found: ...{pix_key[-4:]}")
    try:
        import requests
        # Pixabay requires per_page >= 3
        r = requests.get(
            f"https://pixabay.com/api/videos/?key={pix_key}&q=nature&per_page=3",
            timeout=5
        )
        if r.status_code == 200:
            ok(f"API reachable (HTTP 200)")
            results["pass"] += 1
        else:
            warn(f"Pixabay returned HTTP {r.status_code}")
            results["warn"] += 1
    except Exception as e:
        warn(f"Could not reach Pixabay API: {e}")
        results["warn"] += 1
else:
    warn("Missing PIXABAY_API_KEY (optional, will fallback)")
    results["warn"] += 1

# ─── 7. NewsAPI ───────────────────────────────────────────────────────
print("\n7. NewsAPI")
news_key = os.getenv("NEWS_API_KEY")
if news_key:
    ok(f"Key found: ...{news_key[-4:]}")
    try:
        import requests
        r = requests.get(
            f"https://newsapi.org/v2/everything?q=test&pageSize=1&apiKey={news_key}",
            timeout=5
        )
        if r.status_code == 200:
            ok(f"API reachable (HTTP 200)")
            results["pass"] += 1
        else:
            warn(f"NewsAPI returned HTTP {r.status_code}")
            results["warn"] += 1
    except Exception as e:
        warn(f"Could not reach NewsAPI: {e}")
        results["warn"] += 1
else:
    fail("Missing NEWS_API_KEY")
    results["fail"] += 1

# ─── 8. Font file ─────────────────────────────────────────────────────
print("\n8. Default font file")
font_path = Path(__file__).parent / "packages" / "fonts" / "default_font.ttf"
if font_path.exists():
    ok(f"Font found at: {font_path}")
    results["pass"] += 1
else:
    fail(f"Font not found at {font_path}")
    results["fail"] += 1

# ─── Summary ──────────────────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"Results: {results['pass']} passed, {results['fail']} failed, {results['warn']} warnings")
if results["fail"]:
    print(f"Some keys are MISSING — check .env file or get new keys.")
    sys.exit(1)
else:
    print("All critical keys present.")
    sys.exit(0)
