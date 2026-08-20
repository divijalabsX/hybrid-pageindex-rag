import os

import pytest
from dotenv import load_dotenv


load_dotenv()


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="Gemini API key not available",
)
def test_gemini_page_index_structure():
    from app.llm.gemini_client import generate_page_index_structure

    prompt = """
    Create a simple document hierarchy for a research paper.

    Return JSON with this structure:

    {
      "title": "string",
      "sections": [
        {
          "title": "string",
          "summary": "string"
        }
      ]
    }

    Do not include markdown or explanations.
    """

    response = generate_page_index_structure(prompt)

    assert response