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

print("Gemini JSON response:")
print(response)