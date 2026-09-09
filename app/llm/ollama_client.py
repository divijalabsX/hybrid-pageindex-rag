import json
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "pdurlej/qwythos-9b-claude-mythos-5-1m:latest"


def generate_text(
    prompt: str,
    json_mode: bool = False,
    json_schema=None
) -> str:

    """Generate text using the local Ollama model."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "think": False
    }

    if json_schema is not None:
        payload["format"] = json_schema

    elif json_mode:
        payload["format"] = "json"

    data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["message"]["content"]