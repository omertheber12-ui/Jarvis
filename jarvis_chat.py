#!/usr/bin/env python3
"""
Jarvis terminal chat client.

Prerequisites:
    export OPENAI_API_KEY="sk-..."

Run:
    python jarvis_chat.py
"""

import os
import sys
from typing import List, Dict

from openai import OpenAI

SYSTEM_PROMPT = (
    "You are Jarvis, a helpful personal AI assistant.\n"
    "You communicate concisely, ask clarifying questions when needed, "
    "and help the user manage tasks and decisions.\n"
    "Keep your tone supportive and efficient."
)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

Message = Dict[str, str]


def get_client() -> OpenAI:
    """Instantiate the OpenAI client, ensuring the API key exists."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return OpenAI(api_key=api_key)


def send_message(client: OpenAI, messages: List[Message], model: str = DEFAULT_MODEL) -> str:
    """
    Send the accumulated chat messages to the OpenAI API and return Jarvis's reply.

    Raises RuntimeError if the API call fails.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    return response.choices[0].message.content.strip()


def main() -> None:
    client = get_client()
    messages: List[Message] = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("Jarvis chat started. Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            reply = send_message(client, messages)
        except RuntimeError as err:
            print(f"[Error] {err}", file=sys.stderr)
            # Remove last user message to avoid confusing future context after a failed call.
            messages.pop()
            continue

        print(f"Jarvis: {reply}")
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
