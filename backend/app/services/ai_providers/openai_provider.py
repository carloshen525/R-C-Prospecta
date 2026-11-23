import json
import httpx
from typing import Tuple, Dict, Any, Optional
from app.services.ai_providers.base import BaseAIProvider
from app.core.exceptions import AIProviderException
from app.core.logging import logger

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise AIProviderException("OpenAI API Key não configurada")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(self.base_url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise AIProviderException(f"OpenAI error {res.status_code}: {res.text}")
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            logger.error(f"Falha OpenAI: {e}")
            raise AIProviderException(str(e))

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "API Key não informada"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get("https://api.openai.com/v1/models", headers=headers)
                if res.status_code == 200:
                    return True, "Conexão com OpenAI estabelecida com sucesso"
                return False, f"Falha na autenticação OpenAI: {res.status_code}"
        except Exception as e:
            return False, f"Erro de conexão com OpenAI: {str(e)}"
