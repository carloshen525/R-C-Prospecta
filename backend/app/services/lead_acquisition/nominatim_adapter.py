import httpx
import re
import unicodedata
from typing import List, Dict, Any
from app.services.lead_acquisition.base_adapter import BaseLeadAdapter
from app.core.logging import logger

STOP_WORDS = {"de", "em", "para", "com", "e", "do", "da", "dos", "das", "na", "no"}

KEYWORD_SYNONYMS = {
    "odonto": ["dentista", "clinica odontologica", "consultorio odontologico", "odontologia"],
    "dent": ["dentista", "clinica odontologica", "consultorio odontologico", "odontologia"],
    "medic": ["medico", "consultorio medico", "clinica medica", "saude"],
    "veterin": ["veterinario", "clinica veterinaria", "pet shop"],
    "advoc": ["advogado", "escritorio advocacia"],
    "estet": ["estetica", "salao de beleza", "clinica estetica"],
    "restaur": ["restaurante", "lanchonete", "pizzaria"],
    "oficin": ["oficina mecanica", "auto center"],
    "contab": ["contabilidade", "escritorio contabil"],
    "imobil": ["imobiliaria", "corretor de imoveis"],
    "academ": ["academia", "fitness", "crossfit"],
}

def remove_accents(input_str: str) -> str:
    nfkd = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def generate_search_variants(segment: str) -> List[str]:
    clean_seg = remove_accents(segment.lower()).strip()
    words = [w for w in re.findall(r"\w+", clean_seg) if w not in STOP_WORDS]
    
    variants = [segment.strip()]
    for w in words:
        for prefix, syn_list in KEYWORD_SYNONYMS.items():
            if prefix in w:
                variants.extend(syn_list)
                break
        if len(w) >= 4 and w not in variants:
            variants.append(w)

    # Remove duplicates preserving order
    seen = set()
    deduped = []
    for v in variants:
        v_low = v.lower()
        if v_low not in seen:
            seen.add(v_low)
            deduped.append(v)
    return deduped[:5]

class NominatimAdapter(BaseLeadAdapter):
    """
    Adaptador público baseado em OpenStreetMap / Nominatim.
    Executa busca em múltiplas variações semânticas para cobrir estabelecimentos reais da região.
    """
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "ProspectAI-LeadEngine/1.0 (commercial-prospecting-system)"
        }

    def search(self, segment: str, city: str, state: str, country: str = "Brasil", limit: int = 50) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        seen_keys = set()

        search_variants = generate_search_variants(segment)
        logger.info(f"Iniciando busca Nominatim para '{segment}' em '{city}-{state}'. Variações: {search_variants}")

        for variant in search_variants:
            if len(results) >= limit:
                break

            query = f"{variant} {city} {state}"
            params = {
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "extratags": 1,
                "namedetails": 1,
                "limit": min(30, limit - len(results))
            }

            try:
                with httpx.Client(timeout=15.0) as client:
                    response = client.get(self.base_url, params=params, headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            extratags = item.get("extratags", {}) or {}
                            address = item.get("address", {}) or {}
                            namedetails = item.get("namedetails", {}) or {}
                            
                            company_name = (
                                namedetails.get("name") or
                                item.get("name") or
                                extratags.get("name") or
                                item.get("display_name", "").split(",")[0].strip()
                            )

                            if not company_name or len(company_name) < 3:
                                continue

                            # Chave de unicidade (nome + cidade)
                            key = f"{company_name.lower()}_{city.lower()}"
                            if key in seen_keys:
                                continue
                            seen_keys.add(key)

                            phone = (
                                extratags.get("phone") or
                                extratags.get("contact:phone") or
                                extratags.get("mobile") or
                                extratags.get("contact:mobile")
                            )
                            website = (
                                extratags.get("website") or
                                extratags.get("contact:website") or
                                extratags.get("url")
                            )

                            road = address.get("road") or address.get("street") or address.get("suburb") or ""
                            house_number = address.get("house_number") or ""
                            suburb = address.get("suburb") or address.get("neighbourhood") or ""
                            full_address = f"{road} {house_number}, {suburb}".strip(", ") or item.get("display_name")

                            results.append({
                                "company_name": company_name,
                                "raw_phone": phone,
                                "address": full_address,
                                "city": address.get("city") or address.get("town") or address.get("municipality") or city,
                                "state": address.get("state") or state,
                                "country": address.get("country") or country,
                                "website": website,
                                "category": item.get("type") or segment,
                                "segment": segment,
                                "rating": 4.5,
                                "rating_count": 8,
                                "source": "OpenStreetMap",
                                "description": extratags.get("description")
                            })
                    else:
                        logger.warning(f"Nominatim status {response.status_code} para '{query}'")
            except Exception as e:
                logger.error(f"Erro na busca Nominatim para '{query}': {e}")

        logger.info(f"Nominatim finalizou com {len(results)} estabelecimentos encontrados.")
        return results
