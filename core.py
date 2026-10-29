"""Logique commune (CLI et web) : appels a l'API Gemini."""

import os
import time
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from google import genai
from google.genai import types

ENV_PATH = Path(__file__).resolve().parent / ".env"

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# Modeles de secours si le principal est surcharge (503) ou indisponible (404)
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACKS", "gemini-3.6-flash,gemini-3.5-flash-lite").split(",")
    if m.strip()
]
RETRYABLE_CODES = {429, 500, 502, 503, 504}
ATTEMPTS_PER_MODEL = 2

SYSTEM_PROMPT = (
    "Tu es un assistant utile et poli. Detecte la langue du dernier message de "
    "l'utilisateur (francais, arabe, darija, anglais, espagnol, etc.) et reponds "
    "toujours dans cette meme langue, sauf si l'utilisateur demande explicitement "
    "une autre langue. Sois clair et concis."
)

IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
               "webp": "image/webp"}
TEXT_TYPES = {"txt", "md", "csv", "json", "py"}
ACCEPTED_EXTENSIONS = list(IMAGE_TYPES) + ["pdf"] + sorted(TEXT_TYPES)


def get_client() -> genai.Client:
    # Recharge le .env a chaque appel (meme dossier que core.py, BOM tolere)
    load_dotenv(ENV_PATH, override=True, encoding="utf-8-sig")
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
    if not api_key or api_key == "ta_cle_ici":
        raise RuntimeError(
            f"GEMINI_API_KEY manquante ou invalide. Cree le fichier : {ENV_PATH}"
        )
    return genai.Client(api_key=api_key)


def _config(lang: str | None) -> types.GenerateContentConfig:
    instruction = SYSTEM_PROMPT
    if lang:
        instruction += f" Reponds uniquement en {lang}."
    return types.GenerateContentConfig(system_instruction=instruction, temperature=0.7)


def file_to_part(name: str, data: bytes) -> types.Part:
    """Convertit un fichier envoye par l'utilisateur en Part Gemini."""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext in IMAGE_TYPES:
        return types.Part.from_bytes(data=data, mime_type=IMAGE_TYPES[ext])
    if ext == "pdf":
        return types.Part.from_bytes(data=data, mime_type="application/pdf")
    if ext in TEXT_TYPES:
        text = data.decode("utf-8", errors="replace")
        return types.Part.from_text(text=f"Contenu du fichier {name} :\n{text}")
    raise ValueError(f"Type de fichier non supporte : {name}")


def _models() -> list[str]:
    return [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]


def stream_reply(
    client: genai.Client,
    history: list[dict],
    user_text: str,
    attachments: list[types.Part] | None = None,
    lang: str | None = None,
) -> Iterator[str]:
    """Reponse en streaming, avec nouvelles tentatives et modeles de secours."""
    contents = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in history
    ]
    parts = [types.Part.from_text(text=user_text)] + list(attachments or [])
    contents.append(types.Content(role="user", parts=parts))

    last_exc = None
    for model in _models():
        for attempt in range(ATTEMPTS_PER_MODEL):
            started = False
            try:
                for chunk in client.models.generate_content_stream(
                    model=model, contents=contents, config=_config(lang)
                ):
                    if chunk.text:
                        started = True
                        yield chunk.text
                return
            except Exception as exc:
                code = getattr(exc, "code", None)
                if started or (code not in RETRYABLE_CODES and code != 404):
                    raise
                last_exc = exc
                if code == 404:  # modele indisponible : on passe au suivant
                    break
                time.sleep(1.5 * (attempt + 1))
    raise last_exc


def transcribe(client: genai.Client, audio: bytes, mime_type: str = "audio/wav") -> str:
    """Transcrit un message vocal (dans la langue parlee)."""
    contents = [
        "Transcris fidelement cet audio dans sa langue d'origine. "
        "Reponds uniquement avec la transcription.",
        types.Part.from_bytes(data=audio, mime_type=mime_type),
    ]
    last_exc = None
    for model in _models():
        for attempt in range(ATTEMPTS_PER_MODEL):
            try:
                response = client.models.generate_content(model=model, contents=contents)
                return (response.text or "").strip()
            except Exception as exc:
                code = getattr(exc, "code", None)
                if code not in RETRYABLE_CODES and code != 404:
                    raise
                last_exc = exc
                if code == 404:
                    break
                time.sleep(1.5 * (attempt + 1))
    raise last_exc