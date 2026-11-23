import pytest
from app.services.ai_providers.ai_service import AIService
from app.services.ai_providers.base import BaseAIProvider
from app.core.exceptions import AIProviderException

class MockFailingProvider(BaseAIProvider):
    def generate_json(self, prompt: str, system_prompt: str):
        raise RuntimeError("Quota exceeded 429")
    
    def test_connection(self):
        return False, "Failed"

class MockWorkingProvider(BaseAIProvider):
    def generate_json(self, prompt: str, system_prompt: str):
        return {
            "messages": [
                {"part": 1, "message": "Olá, aqui é o Carlos. Encontrei a clínica no Google Maps."},
                {"part": 2, "message": "Vejo muitos consultórios com horários vagos nas terças e quintas."},
                {"part": 3, "message": "Ajudo empresas com anúncios no Instagram. Podemos conversar 15 min?"}
            ]
        }
    
    def test_connection(self):
        return True, "Ok"

def test_ai_fallback_on_primary_failure():
    service = AIService()
    # Injeta mock de falha no principal (openai) e mock de sucesso no fallback (groq)
    service.providers["openai"] = MockFailingProvider()
    service.providers["groq"] = MockWorkingProvider()
    service.default_provider_name = "openai"
    service.fallback_provider_name = "groq"

    output, provider_used, model = service.generate_sequence_with_fallback(
        prompt="Gerar para Dr. Odonto",
        system_prompt="Prompt do sistema",
        preferred_provider="openai"
    )

    # O provedor utilizado deve ter sido o fallback 'groq'
    assert provider_used == "groq"
    assert len(output.messages) == 3
    assert output.messages[0].part == 1
    assert "Carlos" in output.messages[0].message
