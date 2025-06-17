# app/translator.py
import os
from openai import OpenAI
from openai import RateLimitError, APIError
from typing import List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY", "")


SYSTEM_PROMPT = (
    "You are a helpful translation assistant. "
    "Translate the given English text into Spanish. "
    "Return only the translated text, without additional commentary."
)

# Retry decorator: exponential backoff with jitter, stop after 6 attempts
@retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_random_exponential(min=1, max=60),
    retry=retry_if_exception_type((RateLimitError, APIError)),
)
def _translate_with_backoff(text: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
        max_tokens=256,
        n=1,
    )
    return completion.choices[0].message.content.strip()


def translate_text(text: str) -> str:
    """
    Translate a single text string to Spanish, with retry/backoff on rate limits.
    """
    return _translate_with_backoff(text)


def translate_batch(texts: List[str]) -> List[str]:
    """
    Translate a list of strings, one at a time with backoff.
    """
    return [_translate_with_backoff(txt) for txt in texts]
