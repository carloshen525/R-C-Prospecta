import json
import httpx
from typing import Tuple, Dict, Any, Optional
from app.services.ai_providers.base import BaseAIProvider
from app.core.exceptions import AIProviderException
from app.core.logging import logger

class GroqProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b"):
        self.api_key = api_key
        # Se for modelo descontinuado/inexistente na conta, usa modelo ativo comprovado
        if not model or model == "llama-3.3-70b-versatile":
            self.model = "qwen/qwen3.8-27b"
        else:
            self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise AIProviderException("Groq API Key não configurada")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Modelos a tentar em ordem caso o modelo escolhido falhe com 404 ou 429
        preferred = self.model or "openai/gpt-oss-20b"
        all_models = [preferred, "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        candidate_models = []
        for m in all_models:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for m in candidate_models:
            payload = {
                "model": m,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.7
            }

            try:
                with httpx.Client(timeout=45.0) as client:
                    res = client.post(self.base_url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        content = data["choices"][0]["message"]["content"]
                        # Sanitiza markdown se presente
                        content = content.strip()
                        if content.startswith("```json"):
                            content = content[7:]
                        if content.startswith("```"):
                            content = content[3:]
                        if content.endswith("```"):
                            content = content[:-3]
                        return json.loads(content.strip())
                    elif res.status_code in (400, 404, 429):
                        # Modelo inválido ou rate limit atingido, tenta modelo alternativo na mesma chave
                        logger.warning(f"Groq modelo {m} retornou {res.status_code}. Tentando modelo alternativo...")
                        last_error = f"Groq error {res.status_code}: {res.text}"
                        continue
                    else:
                        raise AIProviderException(f"Groq error {res.status_code}: {res.text}")
            except AIProviderException:
                raise
            except Exception as e:
                logger.error(f"Falha Groq com modelo {m}: {e}")
                last_error = str(e)

        raise AIProviderException(last_error or "Falha ao gerar mensagens com Groq")

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "API Key não informada"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get("https://api.groq.com/openai/v1/models", headers=headers)
                if res.status_code == 200:
                    return True, "Conexão com Groq estabelecida com sucesso"
                return False, f"Falha na autenticação Groq: {res.status_code}"
        except Exception as e:
            return False, f"Erro de conexão com Groq: {str(e)}"
