# app/services/translator.py

import os
import logging
from openai import OpenAI, RateLimitError, APIError
from typing import List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)
_client = None

def _get_openai_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        # Instantiate client only when needed
        _client = OpenAI(api_key=api_key)
    return _client

SYSTEM_PROMPT = (
    "You are a helpful translation assistant. "
    "Translate the given English text into Spanish. "
    "Return only the translated text, without additional commentary."
)

class TranslationError(Exception):
    pass

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(min=1, max=30),
    retry=retry_if_exception_type((RateLimitError, APIError)),
)
def _translate_batch_with_backoff(texts: List[str]) -> List[str]:
    # Only here do we check for the API key and create the client
    client = _get_openai_client()
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(texts)},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        # Split by newline to map back to each input
        translations = completion.choices[0].message.content.split("\n")
        return translations[:len(texts)]
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise TranslationError("API translation failed") from e

def translate_batch(texts: List[str]) -> List[str]:
    """
    Break inputs into batches to respect token limits, then translate each batch.
    """
    MAX_TOKENS = 3000  # rough token estimate
    batches, current, count = [], [], 0

    for text in texts:
        tokens = len(text) // 4
        if current and (count + tokens) > MAX_TOKENS:
            batches.append(current)
            current, count = [], 0
        current.append(text)
        count += tokens

    if current:
        batches.append(current)

    results: List[str] = []
    for batch in batches:
        results.extend(_translate_batch_with_backoff(batch))

    return results
