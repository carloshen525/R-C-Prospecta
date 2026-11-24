import re
import urllib.parse
from typing import List, Dict, Any, Optional
from app.core.logging import logger

class GoogleMapsScraperAdapter:
    """
    Adaptador de extração via navegador web (Playwright Headless Chromium).
    Navega pelo Google Maps público, rola o feed lateral de empresas e extrai
    fichas reais de estabelecimentos (nome, telefone, endereço, site e avaliações).
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def search(
        self,
        segment: str,
        city: str,
        state: str,
        country: str = "Brasil",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        # Prepara a query de pesquisa no Google Maps
        location_parts = [p.strip() for p in [city, state, country] if p and p.strip()]
        full_query = f"{segment} {' '.join(location_parts)}".strip()
        encoded_query = urllib.parse.quote(full_query)
        maps_url = f"https://www.google.com/maps/search/{encoded_query}?hl=pt-BR"

        logger.info(f"[GoogleMapsScraper] Iniciando extração via Chromium para: '{full_query}' (limite={limit})")
        results: List[Dict[str, Any]] = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("[GoogleMapsScraper] Playwright não instalado no ambiente Python.")
            return results

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--no-zygote",
                        "--single-process",
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                context = browser.new_context(
                    locale="pt-BR",
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                # Navega até o Google Maps
                try:
                    page.goto(maps_url, wait_until="domcontentloaded", timeout=25000)
                except Exception as e:
                    logger.warning(f"[GoogleMapsScraper] Timeout ao carregar página: {e}")

                # Lida com modal de cookies / termos de consentimento se aparecer
                for consent_text in ["Aceitar tudo", "Concordo", "Aceitar", "Eu aceito"]:
                    try:
                        btn = page.get_by_text(consent_text, exact=True)
                        if btn.count() > 0 and btn.first.is_visible():
                            btn.first.click()
                            page.wait_for_timeout(1000)
                            break
                    except Exception:
                        pass

                # Aguarda o painel de resultados carregar
                try:
                    page.wait_for_selector('a.hfpxzc, div[role="feed"]', timeout=15000)
                except Exception as e:
                    logger.warning(f"[GoogleMapsScraper] Feed de resultados não apareceu para a busca '{full_query}': {e}")
                    browser.close()
                    return results

                page.wait_for_timeout(1500)

                # Scroll no feed lateral para carregar mais resultados até atingir o limite
                feed_locator = page.locator('div[role="feed"]')
                is_feed_available = feed_locator.count() > 0

                previous_cards_count = 0
                max_scroll_attempts = max(10, (limit // 5) + 3)

                for attempt in range(max_scroll_attempts):
                    current_cards = page.locator("a.hfpxzc").count()
                    if current_cards >= limit:
                        break

                    if is_feed_available:
                        feed_locator.first.evaluate("el => el.scrollBy(0, 2500)")
                    else:
                        page.mouse.wheel(0, 2500)

                    page.wait_for_timeout(1200)

                    # Verifica se o Google indicou o fim da lista
                    end_of_list = page.get_by_text("Você chegou ao final da lista", exact=False).count() > 0
                    if end_of_list:
                        break

                    new_count = page.locator("a.hfpxzc").count()
                    if new_count == previous_cards_count and attempt > 3:
                        # Tenta mais uma rolagem forçada antes de desistir
                        feed_locator.first.evaluate("el => el.scrollBy(0, 4000)")
                        page.wait_for_timeout(1500)
                        if page.locator("a.hfpxzc").count() == previous_cards_count:
                            break
                    previous_cards_count = new_count

                # Coleta as tags dos cards carregados
                card_elements = page.locator("a.hfpxzc").all()
                total_cards = min(len(card_elements), limit)
                logger.info(f"[GoogleMapsScraper] Encontrados {len(card_elements)} cards. Processando {total_cards} fichas...")

                seen_names = set()

                for idx in range(total_cards):
                    try:
                        # Re-localiza o card para evitar stale element reference
                        cards = page.locator("a.hfpxzc").all()
                        if idx >= len(cards):
                            break
                        card = cards[idx]

                        raw_name = card.get_attribute("aria-label") or ""
                        if not raw_name or raw_name.strip() in seen_names:
                            continue

                        # Clica no card para abrir os detalhes no painel lateral
                        card.scroll_into_view_if_needed()
                        card.click()
                        page.wait_for_timeout(1500)

                        company_name = raw_name.strip()
                        seen_names.add(company_name)

                        # 1. Telefone
                        phone = None
                        phone_btns = page.locator('button[data-item-id*="phone"]').all()
                        if phone_btns:
                            # Tenta pelo atributo data-item-id (ex: phone:tel:016991234567)
                            item_id = phone_btns[0].get_attribute("data-item-id") or ""
                            if "phone:tel:" in item_id:
                                phone = item_id.split("phone:tel:")[-1].strip()
                            else:
                                raw_btn_text = phone_btns[0].inner_text()
                                # Limpa ícones especiais e mantém apenas dígitos, parênteses e hífens
                                cleaned = re.sub(r"[^\d\+\(\)\s\-]", "", raw_btn_text).strip()
                                if cleaned:
                                    phone = cleaned

                        # 2. Endereço
                        address = None
                        addr_btns = page.locator('button[data-item-id*="address"]').all()
                        if addr_btns:
                            raw_addr = addr_btns[0].inner_text()
                            cleaned_addr = re.sub(r"^[^\w\s]+", "", raw_addr).strip()
                            if cleaned_addr:
                                address = cleaned_addr

                        # 3. Website
                        website = None
                        web_links = page.locator('a[data-item-id*="authority"]').all()
                        if web_links:
                            website = web_links[0].get_attribute("href")
                        elif page.locator('button[data-item-id*="authority"]').count() > 0:
                            wb = page.locator('button[data-item-id*="authority"]').first
                            website = wb.get_attribute("data-href") or None

                        # 4. Avaliação e contagem de reviews
                        rating = None
                        rating_count = None
                        try:
                            # Busca elemento com a nota (ex: '4,8' ou '5.0')
                            rating_el = page.locator('div.F7nice span[aria-hidden="true"]').first
                            if rating_el.count() > 0:
                                r_text = rating_el.inner_text().strip().replace(",", ".")
                                rating = float(r_text)
                            
                            # Contagem de reviews (ex: '(120)')
                            count_el = page.locator('div.F7nice span[aria-label*="avaliações"], div.F7nice span[aria-label*="reviews"]').first
                            if count_el.count() > 0:
                                count_label = count_el.get_attribute("aria-label") or ""
                                match = re.search(r"(\d+[\.\d]*)", count_label)
                                if match:
                                    rating_count = int(match.group(1).replace(".", ""))
                        except Exception:
                            pass

                        # 5. Categoria / Segmento
                        category = segment
                        try:
                            cat_el = page.locator('button.DkEaL').first
                            if cat_el.count() > 0:
                                category = cat_el.inner_text().strip()
                        except Exception:
                            pass

                        lead_item = {
                            "company_name": company_name,
                            "phone": phone,
                            "raw_phone": phone,
                            "address": address or f"{city}, {state}, {country}",
                            "city": city,
                            "state": state,
                            "country": country,
                            "website": website,
                            "category": category,
                            "segment": segment,
                            "rating": rating,
                            "rating_count": rating_count,
                            "source": "Google Maps (Scraper)",
                            "description": f"Extraído via Google Maps Scraper em {city} - {state}"
                        }

                        results.append(lead_item)
                        logger.info(f"[GoogleMapsScraper] Extraído [{idx+1}/{total_cards}]: {company_name} | Tel: {phone} | Site: {website}")

                    except Exception as card_err:
                        logger.warning(f"[GoogleMapsScraper] Erro ao processar card {idx}: {card_err}")
                        continue

                browser.close()

        except Exception as e:
            logger.error(f"[GoogleMapsScraper] Falha geral durante execução do Playwright: {e}")

        logger.info(f"[GoogleMapsScraper] Concluído. Total de leads extraídos: {len(results)}")
        return results
