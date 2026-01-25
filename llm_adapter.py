import json
import os
from pathlib import Path

from openai import OpenAI

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ask_llm(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)
    config = load_config()
    model = config.get("model", "gpt-4o-mini")

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": "Rispondi in italiano in modo conciso e naturale."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return response.output_text.strip()
