import json
import httpx
from typing import Tuple, Dict, Any, Optional
from app.services.ai_providers.base import BaseAIProvider
from app.core.exceptions import AIProviderException
from app.core.logging import logger

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise AIProviderException("Gemini API Key não configurada")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.7
            }
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    raise AIProviderException(f"Gemini API error {res.status_code}: {res.text}")
                data = res.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception as e:
            logger.error(f"Falha Gemini: {e}")
            raise AIProviderException(str(e))

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "API Key não informada"
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url)
                if res.status_code == 200:
                    return True, "Conexão com Google Gemini estabelecida com sucesso"
                return False, f"Falha na autenticação Gemini: {res.status_code}"
        except Exception as e:
            return False, f"Erro de conexão com Gemini: {str(e)}"
