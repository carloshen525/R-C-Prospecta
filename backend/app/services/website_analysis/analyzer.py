import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from app.services.website_analysis.ssrf_protection import validate_url_safe_for_scraping
from app.core.exceptions import SSRFProtectionException
from app.core.logging import logger

class WebsiteAnalysisService:
    """
    Coleta e sintetiza dados públicos de sites institucionais legítimos.
    Respeita timeouts, protege contra SSRF e extrai informações reais sobre serviços e diferenciais.
    """
    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout = timeout_seconds

    def analyze(self, raw_url: Optional[str]) -> Dict[str, Any]:
        if not raw_url:
            return {"status": "skipped", "reason": "Sem website cadastrado"}

        try:
            safe_url = validate_url_safe_for_scraping(raw_url)
        except SSRFProtectionException as ssrf_err:
            return {"status": "skipped", "reason": str(ssrf_err)}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 ProspectAI-Bot",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                response = client.get(safe_url, headers=headers)
                if response.status_code >= 400:
                    return {
                        "status": "failed",
                        "status_code": response.status_code,
                        "reason": f"HTTP {response.status_code}"
                    }

                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                # Remove tags irrelevantes (scripts, styles, noscript)
                for tag in soup(["script", "style", "noscript", "svg"]):
                    tag.decompose()

                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                
                meta_desc = ""
                desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                if desc_tag and desc_tag.get("content"):
                    meta_desc = desc_tag["content"].strip()

                # Coleta títulos H1 e H2 para identificar principais serviços/proposta de valor
                headings = []
                for h in soup.find_all(["h1", "h2"])[:5]:
                    text = h.get_text(separator=" ", strip=True)
                    if text and len(text) > 3 and len(text) < 120:
                        headings.append(text)

                # Coleta pequeno parágrafo institucional
                paragraphs = []
                for p in soup.find_all("p")[:8]:
                    p_text = p.get_text(separator=" ", strip=True)
                    if len(p_text) > 40:
                        paragraphs.append(p_text)
                
                sample_about = " ".join(paragraphs[:2])[:400] if paragraphs else ""

                # Identifica serviços e produtos a partir de listas e cabeçalhos
                services = []
                for li in soup.find_all("li")[:20]:
                    li_text = li.get_text(strip=True)
                    if 4 < len(li_text) < 60 and not any(skip in li_text.lower() for skip in ["home", "contato", "sobre", "login", "menu", "política", "termos"]):
                        services.append(li_text)

                # Identifica especialidades e tratamentos odontológicos específicos no site
                DENTAL_KEYWORDS = [
                    "implante", "prótese", "alinhador", "invisalign", "ortodontia", "aparelho invisível",
                    "aparelho", "estética dental", "clareamento", "lente de contato", "facetas",
                    "harmonização", "canal", "endodontia", "odontopediatria", "reabilitação oral"
                ]
                combined_text = f"{title} {meta_desc} {' '.join(headings)} {sample_about}".lower()
                detected_specialties = []
                for kw in DENTAL_KEYWORDS:
                    if kw in combined_text and kw not in detected_specialties:
                        detected_specialties.append(kw.capitalize())

                # Se não encontrou em li, usa os headings como serviços principais
                if not services and headings:
                    services = headings[:4]

                summary = meta_desc or sample_about or (title if title else "Site institucional com serviços especializados.")

                return {
                    "status": "success",
                    "url": safe_url,
                    "title": title[:150],
                    "meta_description": meta_desc[:250],
                    "main_headings": headings,
                    "about_summary": sample_about,
                    "summary": summary[:300],
                    "services": services[:6],
                    "detected_specialties": detected_specialties[:5],
                    "products": [s for s in services if any(w in s.lower() for w in ["plano", "produto", "kit", "aparelho", "implante", "prótese"])][:4]
                }

        except Exception as e:
            logger.warning(f"Erro ao analisar website {raw_url}: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }
