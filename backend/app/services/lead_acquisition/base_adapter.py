from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLeadAdapter(ABC):
    @abstractmethod
    def search(self, segment: str, city: str, state: str, country: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Executa a busca de estabelecimentos reais por segmento e localização.
        Retorna lista de dicionários contendo os dados brutos padronizados.
        """
        pass
