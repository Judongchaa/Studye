import os
from openai import OpenAI

from backend.config import (
    MODEL
)


def generate_response(messages_array, model):
    # If environment variable MOCK_LLM is set, return a mock response
    if os.getenv("MOCK_LLM") == "1":
        return "This is a mock assistant response for testing."

    api_key = os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        raise ValueError("OPEN_AI_API_KEY environment variable is not set")

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    if MODEL.get("think") == model:
        response = client.chat.completions.create(
            model=model, 
            messages=messages_array,    
            max_completion_tokens=64000,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
    else:
        response = client.chat.completions.create(
            model=model, 
            messages=messages_array,    
            max_completion_tokens=128000,
        )
    return response.choices[0].message.content
