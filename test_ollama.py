import litellm

response = litellm.completion(
    model="ollama/qwen3.5:0.8b",
    messages=[
        {
            "role": "user",
            "content": "Explain artificial intelligence in one sentence."
        }
    ],
    api_base="http://localhost:11434"
)

print(response.choices[0].message.content)