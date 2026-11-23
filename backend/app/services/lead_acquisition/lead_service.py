import re
import time
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.campaign_lead import CampaignLead
from app.models.campaign import Campaign
from app.models.suppression_list import SuppressionList
from app.models.extraction_job import ExtractionJob
from app.models.setting import Setting
from app.config import settings
from app.services.lead_acquisition.nominatim_adapter import NominatimAdapter
from app.services.lead_acquisition.google_places_adapter import GooglePlacesAdapter
from app.services.lead_acquisition.google_maps_scraper_adapter import GoogleMapsScraperAdapter
from app.core.logging import logger

def normalize_phone_e164(raw_phone: Optional[str], default_country_code: str = "55") -> Optional[str]:
    """
    Normaliza telefones brasileiros e internacionais para o formato E.164.
    Ex: '(16) 99123-4567' -> '+5516991234567'
        '1636250000' -> '+551636250000'
    """
    if not raw_phone:
        return None
    
    # Remove caracteres não numéricos
    digits = re.sub(r"[^\d]", "", raw_phone)
    if not digits:
        return None

    # Se começa com 0 na frente do DDD (ex: 016991234567), remove o zero inicial
    if digits.startswith("0") and len(digits) in (11, 12):
        digits = digits[1:]

    # Se tem 10 ou 11 dígitos, é número brasileiro sem código do país
    if len(digits) in (10, 11):
        digits = f"{default_country_code}{digits}"
    
    return f"+{digits}"

def is_phone_suppressed(db: Session, normalized_phone: str) -> bool:
    """Verifica se o telefone está na lista de supressão/bloqueio"""
    if not normalized_phone:
        return False
    return db.query(SuppressionList).filter(SuppressionList.phone == normalized_phone).first() is not None

class LeadAcquisitionService:
    def __init__(self, db: Session, google_maps_api_key: Optional[str] = None):
        self.db = db
        
        # Recupera chave da Google Places API do banco de configurações ou do .env se não passada
        if not google_maps_api_key:
            key_setting = db.query(Setting).filter(Setting.key == "GOOGLE_MAPS_API_KEY").first()
            if key_setting and key_setting.value:
                google_maps_api_key = key_setting.value.strip()
            elif getattr(settings, "GOOGLE_MAPS_API_KEY", None):
                google_maps_api_key = settings.GOOGLE_MAPS_API_KEY.strip()

        self.google_places_adapter = GooglePlacesAdapter(api_key=google_maps_api_key)
        self.nominatim_adapter = NominatimAdapter()
        self.google_maps_scraper_adapter = GoogleMapsScraperAdapter()

    def execute_extraction(self, job_id: int) -> ExtractionJob:
        job = self.db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} não encontrado")

        job.status = "running"
        self.db.commit()
        start_time = time.time()

        raw_leads: List[Dict[str, Any]] = []

        try:
            selected_source = getattr(job, "source", None) or "google_scraper"
            logger.info(f"Job {job_id}: Executando com motor '{selected_source}' para '{job.segment}' em {job.city}-{job.state}")

            if selected_source == "google_places":
                if not self.google_places_adapter.api_key:
                    raise ValueError("Chave da Google Places API não está configurada em Configurações.")
                raw_leads = self.google_places_adapter.search(
                    segment=job.segment,
                    city=job.city,
                    state=job.state,
                    country=job.country,
                    limit=job.desired_qty
                )
            elif selected_source == "openstreetmap":
                raw_leads = self.nominatim_adapter.search(
                    segment=job.segment,
                    city=job.city,
                    state=job.state,
                    country=job.country,
                    limit=job.desired_qty
                )
            elif selected_source == "auto":
                if self.google_places_adapter.api_key:
                    raw_leads = self.google_places_adapter.search(
                        segment=job.segment,
                        city=job.city,
                        state=job.state,
                        country=job.country,
                        limit=job.desired_qty
                    )
                else:
                    raw_leads = self.google_maps_scraper_adapter.search(
                        segment=job.segment,
                        city=job.city,
                        state=job.state,
                        country=job.country,
                        limit=job.desired_qty
                    )
                if not raw_leads:
                    raw_leads = self.nominatim_adapter.search(
                        segment=job.segment,
                        city=job.city,
                        state=job.state,
                        country=job.country,
                        limit=job.desired_qty
                    )
            else:  # "google_scraper"
                raw_leads = self.google_maps_scraper_adapter.search(
                    segment=job.segment,
                    city=job.city,
                    state=job.state,
                    country=job.country,
                    limit=job.desired_qty
                )
                if not raw_leads:
                    logger.info(f"Job {job_id}: Scraper não retornou itens. Tentando fallback...")
                    if self.google_places_adapter.api_key:
                        raw_leads = self.google_places_adapter.search(
                            segment=job.segment,
                            city=job.city,
                            state=job.state,
                            country=job.country,
                            limit=job.desired_qty
                        )
                    else:
                        raw_leads = self.nominatim_adapter.search(
                            segment=job.segment,
                            city=job.city,
                            state=job.state,
                            country=job.country,
                            limit=job.desired_qty
                        )

            # Estrutura os itens extraídos para curadoria e seleção do usuário
            items: List[Dict[str, Any]] = []
            filtered_no_phone = 0
            filtered_no_website = 0

            for idx, raw in enumerate(raw_leads):
                raw_phone = raw.get("raw_phone")
                norm_phone = normalize_phone_e164(raw_phone)
                website = raw.get("website")
                company_name = (raw.get("company_name") or "").strip()

                if not company_name:
                    continue

                if job.has_phone_filter and not norm_phone:
                    filtered_no_phone += 1
                    continue
                if job.has_website_filter and not website:
                    filtered_no_website += 1
                    continue

                items.append({
                    "index": len(items),
                    "company_name": company_name,
                    "phone": norm_phone,
                    "raw_phone": raw_phone,
                    "address": raw.get("address") or f"{job.city}, {job.state}, {job.country}",
                    "city": raw.get("city") or job.city,
                    "state": raw.get("state") or job.state,
                    "country": raw.get("country") or job.country,
                    "website": website,
                    "rating": raw.get("rating"),
                    "rating_count": raw.get("rating_count"),
                    "category": raw.get("category") or job.segment,
                    "source": raw.get("source", "Google Maps"),
                    "is_imported": False,
                    "lead_id": None
                })

            job.extracted_items = items
            job.found_count = len(items)
            job.processed_count = len(items)
            job.saved_count = 0
            job.execution_time_seconds = round(time.time() - start_time, 2)
            job.status = "completed"

            # Se auto_import estiver ativado, importa automaticamente todos os itens elegíveis
            if getattr(job, "auto_import", False):
                self.import_selected_leads(
                    job_id=job.id,
                    selected_indices=list(range(len(items))),
                    campaign_id=job.campaign_id
                )

            # Diagnóstico
            if len(items) == 0:
                if len(raw_leads) == 0:
                    job.error_log = f"Nenhum estabelecimento encontrado para '{job.segment}' em '{job.city}-{job.state}'."
                elif filtered_no_phone > 0:
                    job.error_log = f"{filtered_no_phone} estabelecimentos encontrados, mas descartados pelo filtro 'Apenas com telefone'."
            else:
                job.error_log = None

            self.db.commit()

        except Exception as job_err:
            self.db.rollback()
            job.status = "failed"
            job.error_log = str(job_err)
            job.execution_time_seconds = round(time.time() - start_time, 2)
            self.db.commit()
            logger.error(f"Falha na extração job {job_id}: {job_err}")

        return job

    def import_selected_leads(
        self,
        job_id: int,
        selected_indices: List[int],
        campaign_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Importa seletivamente os leads aprovados pelo usuário para a base oficial
        de leads e vincula à campanha escolhida.
        """
        job = self.db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} não encontrado")

        items = list(job.extracted_items or [])
        target_campaign_id = campaign_id if campaign_id is not None else job.campaign_id

        imported_now = 0
        duplicate_count = 0

        for idx in selected_indices:
            if idx < 0 or idx >= len(items):
                continue
            item = items[idx]

            company_name = item.get("company_name", "").strip()
            norm_phone = item.get("phone")
            raw_phone = item.get("raw_phone")
            website = item.get("website")

            if not company_name:
                continue

            # Deduplicação inteligente
            existing_lead = None
            if norm_phone:
                existing_lead = self.db.query(Lead).filter(Lead.phone == norm_phone).first()
            if not existing_lead:
                existing_lead = self.db.query(Lead).filter(
                    Lead.company_name.ilike(company_name),
                    Lead.city.ilike(item.get("city") or job.city)
                ).first()

            suppressed = is_phone_suppressed(self.db, norm_phone) if norm_phone else False

            if existing_lead:
                duplicate_count += 1
                if website and not existing_lead.website:
                    existing_lead.website = website
                if item.get("rating") and not existing_lead.rating:
                    existing_lead.rating = item.get("rating")
                target_lead = existing_lead
            else:
                target_lead = Lead(
                    user_id=job.user_id,
                    company_name=company_name,
                    phone=norm_phone,
                    raw_phone=raw_phone,
                    address=item.get("address"),
                    city=item.get("city") or job.city,
                    state=item.get("state") or job.state,
                    country=item.get("country") or job.country,
                    website=website,
                    category=item.get("category"),
                    segment=job.segment,
                    rating=item.get("rating"),
                    rating_count=item.get("rating_count"),
                    source=item.get("source", "Google Maps"),
                    status="nao_contatar" if suppressed else "novo",
                    is_eligible=not suppressed,
                )
                self.db.add(target_lead)
                self.db.flush()

            # Vincula à automação global contínua
            if not target_campaign_id:
                from app.api.v1.endpoints.automation import get_or_create_system_campaign
                default_camp = get_or_create_system_campaign(self.db)
                target_campaign_id = default_camp.id

            if target_campaign_id and target_lead.is_eligible and target_lead.phone:
                assoc = self.db.query(CampaignLead).filter(
                    CampaignLead.campaign_id == target_campaign_id,
                    CampaignLead.lead_id == target_lead.id
                ).first()
                if not assoc:
                    assoc = CampaignLead(
                        campaign_id=target_campaign_id,
                        lead_id=target_lead.id,
                        status="aguardando"
                    )
                    self.db.add(assoc)

            item["is_imported"] = True
            item["lead_id"] = target_lead.id
            imported_now += 1

        # Atualiza o registro do job
        job.extracted_items = items
        job.saved_count = sum(1 for it in items if it.get("is_imported"))
        job.duplicate_count += duplicate_count
        self.db.commit()

        logger.info(f"Job {job_id}: {imported_now} leads importados com sucesso para a base (Campanha: {target_campaign_id})")
        return {
            "imported_count": imported_now,
            "total_saved": job.saved_count,
            "duplicate_count": duplicate_count
        }

        return job
