# app/translator.py
import os
import logging
from openai import OpenAI
from openai import RateLimitError, APIError
from typing import List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set")

client = OpenAI()
client.api_key = api_key
logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a helpful translation assistant. "
    "Translate the given English text into Spanish. "
    "Return only the translated text, without additional commentary."
)

class TranslationError(Exception):
    pass

# Retry decorator: exponential backoff with jitter, stop after 6 attempts
@retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_random_exponential(min=1, max=60),
    retry=retry_if_exception_type((RateLimitError, APIError)),
)
def _translate_batch_with_backoff(texts: List[str]) -> List[str]:
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(texts)}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        translations = completion.choices[0].message.content.split("\n")
        return translations[:len(texts)]  # Safety check
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise TranslationError("API translation failed") from e


def translate_batch(texts: List[str]) -> List[str]:
    """Smart batching respecting token limits"""
    MAX_TOKENS = 3000
    batches = []
    current_batch = []
    current_count = 0
    
    for text in texts:
        tokens = len(text) // 4  # Approximate token count
        if current_count + tokens > MAX_TOKENS and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_count = 0
        current_batch.append(text)
        current_count += tokens
    
    if current_batch:
        batches.append(current_batch)
    
    results = []
    for batch in batches:
        results.extend(_translate_batch_with_backoff(batch))
    return results
