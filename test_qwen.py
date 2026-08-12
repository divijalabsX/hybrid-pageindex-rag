from transformers import pipeline

print("Loading Qwen3.5-0.8B...")

pipe = pipeline(
    "image-text-to-text",
    model="Qwen/Qwen3.5-0.8B"
)

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What is artificial intelligence? Explain in two sentences."
            }
        ]
    }
]

result = pipe(text=messages)

print("\nQwen response:")
print(result)