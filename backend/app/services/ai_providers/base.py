from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class BaseAIProvider(ABC):
    @abstractmethod
    def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Gera resposta em formato JSON estruturado"""
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Testa conectividade e validação da API Key com o provedor"""
        pass
