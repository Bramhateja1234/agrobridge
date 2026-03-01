import google.generativeai as genai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash") # Using flash for faster/cheaper responses
        else:
            self.model = None
            logger.error("GEMINI_API_KEY not found in settings.")

    def generate_json(self, prompt, fallback=None):
        if not self.model:
            return fallback or {"error": "AI service not configured"}
        
        try:
            # Adding strict instruction to the prompt
            full_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON. No preamble, no markdown formatting blocks, no extra text."
            response = self.model.generate_content(full_prompt)
            
            text = response.text.strip()
            # Basic cleaning in case the model wraps it in markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return fallback or {"error": "AI service unavailable"}
