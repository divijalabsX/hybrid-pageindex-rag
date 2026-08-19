import os
import pytest


@pytest.mark.skipif(
    os.getenv("RUN_OLLAMA_TESTS") != "1",
    reason="Ollama integration test disabled in CI",
)
def test_ollama_completion():
    import litellm

    response = litellm.completion(
        model="ollama/qwen3.5:0.8b",
        messages=[
            {
                "role": "user",
                "content": "Explain artificial intelligence in one sentence.",
            }
        ],
        api_base="http://localhost:11434",
    )

    assert response.choices[0].message.content