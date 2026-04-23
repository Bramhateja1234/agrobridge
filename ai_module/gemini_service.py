from google import genai
from google.genai import types
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext as _
import json
import logging
import hashlib
import time
import uuid

logger = logging.getLogger(__name__)

_THROTTLE_SECONDS = 3

def _is_allowed(user_key, prompt_type, model_name):
    """Returns True if user is allowed to make AI call (not throttled). Uses multi-dimensional throttling."""
    cache_throttle_key = f"throttle_ai_{user_key}_{prompt_type}_{model_name}"
    last_call = cache.get(cache_throttle_key)
    
    now = time.time()
    if last_call and (now - last_call) < _THROTTLE_SECONDS:
        return False
        
    cache.set(cache_throttle_key, now, timeout=_THROTTLE_SECONDS)
    return True


def _get_cache_key(prompt, lang):
    raw = f"{prompt}_{lang}"
    return "gemini_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _get_ttl(prompt_type):
    if prompt_type == "weather":
        return 600  # 10 min
    if prompt_type == "crop":
        return 1800 # 30 min
    return 900      # 15 min

class GeminiService:
    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            # We explicitly configure a timeout in the HTTP layer to prevent hanging SDK calls
            self.client = genai.Client(api_key=api_key, http_options={'timeout': 10000}) 
            self.model_name = "gemini-flash-latest"
        else:
            self.client = None
            logger.error("GEMINI_API_KEY not found in settings.")

    def _generate_with_retry(self, full_prompt, request_id):
        last_exception = None
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                return response.text.strip()
            except Exception as e:
                last_exception = e
                if attempt == 2:
                    logger.error(f"[{request_id}] Gemini failure after 3 attempts.", exc_info=True)
                    raise
                wait = 1.5 * (attempt + 1)
                logger.warning(f"[{request_id}] Retry attempt {attempt + 1} triggered: {str(e)}. Waiting {wait}s.")
                time.sleep(wait)
        raise last_exception

    def generate_json(self, prompt, fallback=None, lang="en", user_key="anonymous", prompt_type="generic"):
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] AI request start")

        if not self.client:
            return fallback or {"error": _("AI service not configured")}

        # --- Fix 3: Distributed Throttling Key Design ---
        if not _is_allowed(user_key, prompt_type, self.model_name):
            logger.warning(f"[{request_id}] Throttle triggered for user: {user_key}, type: {prompt_type}")
            return fallback or {"error": _("Too many requests. Please wait a moment.")}

        cache_key = _get_cache_key(prompt, lang)
        lock_key = f"lock_{cache_key}"

        # --- Fix 1 & 2: Request Coalescing (Fan-Out) and Cache Stampede Window ---
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"[{request_id}] Cache hit immediate")
            return cached_result
            
        # If someone else is computing, wait a bit for the cache to fill
        if cache.get(lock_key):
            logger.info(f"[{request_id}] Concurrent request detected. Waiting for lock release.")
            waited = 0
            wait_ms = 3000
            step_ms = 300
            while waited < wait_ms:
                time.sleep(step_ms / 1000.0)
                waited += step_ms
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"[{request_id}] Cache hit after waiting")
                    return cached_result
            
            # Context-aware fallback if it times out waiting
            logger.warning(f"[{request_id}] Timed out waiting for cache lock.")
            if fallback:
                return fallback
            return {
                "advice": _("Unable to fetch AI response at this moment. Please base decisions on local observation and general best practices."),
                "confidence": "low"
            }
            
        # Acquire lock to perform the computation
        cache.set(lock_key, True, timeout=15)

        full_prompt = f"{prompt}\n\nIMPORTANT: Return valid JSON. Respond entirely in language ISO code: '{lang}'."

        try:
            logger.info(f"[{request_id}] Starting model generation")
            text = self._generate_with_retry(full_prompt, request_id)

            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            parsed_result = json.loads(text)
            
            # --- Fix 5: Data-Sensitive TTL Cache Invalidation ---
            ttl = _get_ttl(prompt_type)
            cache.set(cache_key, parsed_result, timeout=ttl)
            
            # Free the lock immediately
            cache.delete(lock_key)
            logger.info(f"[{request_id}] Generation successful and cached with TTL {ttl}s")
            return parsed_result

        except Exception as e:
            cache.delete(lock_key)
            logger.error(f"[{request_id}] Failed to generate/parse Gemini JSON: {str(e)}")
            
            # --- Fix 7: Context-aware fallback ---
            if fallback:
                return fallback
            return {
                "advice": _("Unable to fetch AI response at this moment. Please base decisions on local observation and general best practices."),
                "confidence": "low"
            }
