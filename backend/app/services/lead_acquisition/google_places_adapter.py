import httpx
from typing import List, Dict, Any, Optional, Tuple
from app.services.lead_acquisition.base_adapter import BaseLeadAdapter
from app.core.logging import logger

class GooglePlacesAdapter(BaseLeadAdapter):
    """
    Adaptador oficial para Google Places API (Google Maps Platform).
    Utiliza as APIs oficiais Text Search e Place Details para extrair
    estabelecimentos reais com telefone, website, avaliações e localização exata.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key:
            return False, "Google Places API Key não informada"
        
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": "restaurante em Sao Paulo",
            "key": self.api_key
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    status = data.get("status")
                    if status in ("OK", "ZERO_RESULTS"):
                        return True, "Conexão com Google Places API validada com sucesso!"
                    elif status == "REQUEST_DENIED":
                        error_msg = data.get("error_message") or "Chave inválida ou Places API não ativada no Google Cloud Console"
                        return False, f"Google Places recusado: {error_msg}"
                    else:
                        return False, f"Resposta Google Places: {status}"
                return False, f"Erro HTTP {res.status_code}"
        except Exception as e:
            return False, f"Falha de conexão: {str(e)}"

    def search(self, segment: str, city: str, state: str, country: str = "Brasil", limit: int = 50) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not self.api_key:
            logger.info("Chave do Google Places API não informada. Pulando adaptador oficial do Google Places.")
            return results

        query = f"{segment} em {city}, {state}, {country}"
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": self.api_key,
            "language": "pt-BR"
        }

        try:
            logger.info(f"Executando pesquisa oficial no Google Places: '{query}'")
            with httpx.Client(timeout=25.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("results", [])
                    logger.info(f"Google Places retornou {len(places)} locais brutos.")

                    for p in places[:limit]:
                        place_id = p.get("place_id")
                        name = p.get("name")
                        address = p.get("formatted_address")
                        rating = p.get("rating")
                        rating_count = p.get("user_ratings_total")

                        # Busca detalhes para obter telefone oficial e website
                        phone = None
                        website = None
                        if place_id:
                            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                            det_resp = client.get(details_url, params={
                                "place_id": place_id,
                                "fields": "formatted_phone_number,international_phone_number,website,geometry",
                                "key": self.api_key,
                                "language": "pt-BR"
                            })
                            if det_resp.status_code == 200:
                                det_data = det_resp.json().get("result", {})
                                phone = det_data.get("international_phone_number") or det_data.get("formatted_phone_number")
                                website = det_data.get("website")

                        results.append({
                            "company_name": name,
                            "raw_phone": phone,
                            "address": address,
                            "city": city,
                            "state": state,
                            "country": country,
                            "website": website,
                            "category": segment,
                            "segment": segment,
                            "rating": rating,
                            "rating_count": rating_count,
                            "source": "Google Maps",
                            "description": None
                        })
                else:
                    logger.error(f"Erro HTTP na consulta Google Places API: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Exceção na consulta Google Places API: {e}")

        return results
