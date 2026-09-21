from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from pipeline.paths import ENV_PATH


API = "https://api.kie.ai/api/v1"


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def load_api_key() -> str:
    load_dotenv(ENV_PATH, encoding="utf-8-sig", override=True)
    key = (os.getenv("KIE_API_KEY") or "").strip().strip('"').strip("'")
    if key:
        return key
    if not ENV_PATH.exists():
        return ""
    for line in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "KIE_API_KEY":
            return value.strip().strip('"').strip("'")
    return ""


def generate_instrumental(dest: Path, cfg: dict, duration_sec: float) -> Path:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError(
            "Нет ключа Kie AI. Скопируйте .env.example в .env и вставьте KIE_API_KEY."
        )
    kie = cfg.get("kie") or {}
    model = kie.get("model") or "V4_5"
    payload = {
        "prompt": (
            f"Instrumental sports highlight, about {int(duration_sec)} seconds, "
            + (
                "no singing, elegant tension, sparse drums, slow build for balance holds"
                if (cfg.get("routine_style") == "balance")
                else "no singing, cinematic drums, rising tension then punch"
            )
        ),
        "customMode": True,
        "instrumental": True,
        "model": model,
        "style": (
            kie.get(f"style_{cfg.get('routine_style')}")
            or kie.get("style")
            or "cinematic sports trailer, no vocals"
        ),
        "title": (kie.get("title") or "Acro Highlight")[:80],
        "negativeTags": kie.get("negative_tags") or "vocals, lyrics",
        "callBackUrl": "https://example.com/kie-callback",
    }
    resp = requests.post(f"{API}/generate", headers=_headers(api_key), json=payload, timeout=60)
    body = resp.json() if resp.content else {}
    if resp.status_code != 200 or body.get("code") != 200:
        raise RuntimeError(f"Kie AI не принял задачу: {resp.status_code} {body}")
    task_id = (body.get("data") or {}).get("taskId")
    if not task_id:
        raise RuntimeError(f"Kie AI не вернул taskId: {body}")

    timeout = float(kie.get("timeout_seconds", 480))
    poll = float(kie.get("poll_seconds", 12))
    started = time.time()
    audio_url = None
    while time.time() - started < timeout:
        info = requests.get(
            f"{API}/generate/record-info",
            headers=_headers(api_key),
            params={"taskId": task_id},
            timeout=60,
        )
        data = info.json() if info.content else {}
        if info.status_code != 200 or data.get("code") != 200:
            time.sleep(poll)
            continue
        status = ((data.get("data") or {}).get("status") or "").upper()
        tracks = ((data.get("data") or {}).get("response") or {}).get("sunoData") or []
        if status in {"SUCCESS", "FIRST_SUCCESS"} and tracks:
            audio_url = tracks[0].get("audio_url") or tracks[0].get("audioUrl")
            break
        if status in {
            "CREATE_TASK_FAILED",
            "GENERATE_AUDIO_FAILED",
            "SENSITIVE_WORD_ERROR",
            "CALLBACK_EXCEPTION",
        }:
            raise RuntimeError(f"Kie AI ошибка генерации: {status} {data}")
        time.sleep(poll)

    if not audio_url:
        raise RuntimeError("Kie AI не успел отдать музыку. Можно положить свой mp3 в папку music.")

    dest.parent.mkdir(parents=True, exist_ok=True)
    audio = requests.get(audio_url, timeout=120)
    audio.raise_for_status()
    dest.write_bytes(audio.content)
    return dest
