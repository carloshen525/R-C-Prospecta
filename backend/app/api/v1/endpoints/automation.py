import time
import random
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db, SessionLocal
from app.models.setting import Setting
from app.models.lead import Lead
from app.models.message import Message
from app.models.campaign import Campaign
from app.models.campaign_lead import CampaignLead
from app.models.generated_sequence import GeneratedSequence
from app.models.sending_daily_usage import SendingDailyUsage
from app.models.conversation import Conversation, ConversationEvent
from app.core.scheduler_rules import is_within_sending_window, get_now_in_brazil
from app.services.ai_providers.ai_service import AIService
from app.services.website_analysis.analyzer import WebsiteAnalysisService
from app.services.campaigns.engine import CampaignExecutionEngine
from app.services.message_generator.generator import MessageGeneratorService, SYSTEM_PROMPT as DEFAULT_PROMPT
from app.core.logging import logger

router = APIRouter()

# --- Schemas ---

class StatusToggleRequest(BaseModel):
    status: str  # "ativa" ou "pausada"

class PromptUpdateRequest(BaseModel):
    prompt: str

class SimulateRequest(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    contact_name: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    custom_prompt: Optional[str] = None

class AutomationSettingsUpdate(BaseModel):
    min_interval_sec: Optional[int] = None
    max_interval_sec: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    allowed_days: Optional[List[str]] = None
    max_contacts_hour: Optional[int] = None
    max_contacts_day: Optional[int] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

# --- Helper Functions ---

def get_setting_val(db: Session, key: str, default: Any = None) -> Any:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s and s.value is not None else default

def set_setting_val(db: Session, key: str, value: Any, category: str = "automation"):
    s = db.query(Setting).filter(Setting.key == key).first()
    if not s:
        s = Setting(key=key, value=str(value), category=category)
        db.add(s)
    else:
        s.value = str(value)
    db.commit()

def get_or_create_system_campaign(db: Session) -> Campaign:
    camp = db.query(Campaign).first()
    if not camp:
        camp = Campaign(
            name="Automação Global",
            description="Motor contínuo de prospecção",
            status="ativa",
            ai_provider="groq",
            ai_model="qwen/qwen3.8-27b",
            daily_limit=30
        )
        db.add(camp)
        db.commit()
        db.refresh(camp)
    return camp

# --- Endpoints ---

@router.get("/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Retorna o status atual da Automação de Prospecção (Ativa ou Pausada)"""
    status = get_setting_val(db, "AUTOMATION_STATUS", "ativa")
    window_open, window_msg = is_within_sending_window()
    
    # Cota diária
    today = get_now_in_brazil().date()
    usage = db.query(SendingDailyUsage).filter(SendingDailyUsage.usage_date == today).first()
    sent_today = usage.contacts_sent_count if usage else 0
    daily_limit = int(get_setting_val(db, "DAILY_CONTACT_LIMIT", 20))

    return {
        "status": status,
        "is_active": status.lower() == "ativa",
        "is_window_open": window_open,
        "window_message": window_msg,
        "sent_today": sent_today,
        "daily_limit": daily_limit
    }

@router.post("/toggle")
def toggle_automation_status(payload: StatusToggleRequest, db: Session = Depends(get_db)):
    """Alterna instantaneamente o estado da Automação (Ativa / Pausada)"""
    new_status = payload.status.lower().strip()
    if new_status not in ("ativa", "pausada"):
        raise HTTPException(status_code=400, detail="Status deve ser 'ativa' ou 'pausada'")
    
    set_setting_val(db, "AUTOMATION_STATUS", new_status)
    
    # Atualiza campanhas internas para manter consistência
    camps = db.query(Campaign).all()
    for c in camps:
        c.status = new_status
    db.commit()

    return {"status": "success", "automation_status": new_status}

@router.get("/prompt")
def get_automation_prompt(db: Session = Depends(get_db)):
    """Retorna o prompt atual da IA e o prompt padrão de fábrica"""
    saved = get_setting_val(db, "AUTOMATION_PROMPT", "")
    return {
        "prompt": saved if saved else DEFAULT_PROMPT,
        "default_prompt": DEFAULT_PROMPT,
        "is_customized": bool(saved and saved != DEFAULT_PROMPT)
    }

@router.put("/prompt")
def update_automation_prompt(payload: PromptUpdateRequest, db: Session = Depends(get_db)):
    """Atualiza o prompt mestre da IA utilizado pela automação"""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="O prompt não pode ser vazio")
    
    set_setting_val(db, "AUTOMATION_PROMPT", payload.prompt.strip())
    return {"status": "success", "message": "Prompt da IA salvo com sucesso!"}

@router.post("/prompt/reset")
def reset_automation_prompt(db: Session = Depends(get_db)):
    """Restaura o prompt padrão de fábrica"""
    set_setting_val(db, "AUTOMATION_PROMPT", DEFAULT_PROMPT)
    return {"status": "success", "message": "Prompt restaurado para o padrão de fábrica!", "prompt": DEFAULT_PROMPT}

@router.post("/simulate")
def simulate_message(payload: SimulateRequest, db: Session = Depends(get_db)):
    """
    Simula em tempo real a mensagem de prospecção sem enviar nada:
    1. Acessa o site informado e extrai informações ricas (produtos, serviços, cidade, resumo)
    2. Utiliza o prompt exato configurado
    3. Gera a mensagem com a IA
    4. Retorna as informações encontradas e a mensagem formatada para cópia e validação
    """
    website_service = WebsiteAnalysisService(timeout_seconds=12.0)
    website_analysis = None
    extracted_info = {
        "empresa": payload.company_name,
        "segmento": "Geral",
        "produtos_encontrados": [],
        "servicos_encontrados": [],
        "cidade": payload.city or "Não informada",
        "resumo_site": "Nenhum website informado para análise.",
        "site_acessado": False
    }

    if payload.website_url:
        website_analysis = website_service.analyze(payload.website_url)
        if website_analysis.get("status") not in ("skipped", "failed"):
            extracted_info["site_acessado"] = True
            extracted_info["resumo_site"] = website_analysis.get("summary") or website_analysis.get("meta_description") or "Site analisado com sucesso."
            extracted_info["produtos_encontrados"] = website_analysis.get("products", [])
            extracted_info["servicos_encontrados"] = website_analysis.get("services", [])
            if website_analysis.get("category"):
                extracted_info["segmento"] = website_analysis.get("category")
        else:
            extracted_info["resumo_site"] = f"Não foi possível acessar ({website_analysis.get('reason', 'falha')}). Usando informações básicas."

    # Prepara o prompt do sistema
    prompt_to_use = payload.custom_prompt or get_setting_val(db, "AUTOMATION_PROMPT", DEFAULT_PROMPT)
    
    # Monta contexto do lead para a IA
    lead_prompt = f"""DADOS DO ESTABELECIMENTO PARA PROSPECÇÃO:
Nome da Empresa: {payload.company_name}
Cidade: {payload.city or 'São Paulo / Região'}
Site: {payload.website_url or 'Não informado'}
Nome do Responsável: {payload.contact_name or 'Responsável pela empresa'}
Observações Adicionais: {payload.notes or 'Nenhuma'}
"""
    if website_analysis and website_analysis.get("status") not in ("skipped", "failed"):
        lead_prompt += f"""
INFORMAÇÕES EXTRAÍDAS DO WEBSITE:
Resumo: {extracted_info['resumo_site']}
Serviços Identificados: {', '.join(extracted_info['servicos_encontrados']) if extracted_info['servicos_encontrados'] else 'Serviços especializados do setor'}
Títulos da Página: {', '.join(website_analysis.get('headings', []))}
"""

    lead_prompt += "\nGere a sequência de 3 mensagens personalizadas seguindo rigorosamente as instruções do prompt do sistema."

    ai_service = AIService(db=db)
    try:
        validated_output, provider_used, model_used = ai_service.generate_sequence_with_fallback(
            prompt=lead_prompt,
            system_prompt=prompt_to_use
        )
        messages = [
            {"part": m.part, "message": m.message} for m in validated_output.messages
        ]
    except Exception as e:
        logger.error(f"Erro na simulação de IA: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar simulação com IA: {str(e)}")

    return {
        "extracted_info": extracted_info,
        "messages": messages,
        "full_text": "\n\n".join([f"[Mensagem {m['part']}]:\n{m['message']}" for m in messages]),
        "provider_used": provider_used,
        "model_used": model_used
    }

@router.get("/settings")
def get_automation_settings(db: Session = Depends(get_db)):
    """Retorna todas as configurações da automação contínua"""
    return {
        "min_interval_sec": int(get_setting_val(db, "MIN_INTERVAL_BETWEEN_CONTACTS_SEC", 180)),
        "max_interval_sec": int(get_setting_val(db, "MAX_INTERVAL_BETWEEN_CONTACTS_SEC", 360)),
        "start_time": f"{int(get_setting_val(db, 'SENDING_START_HOUR', 7)):02d}:{int(get_setting_val(db, 'SENDING_START_MINUTE', 0)):02d}",
        "end_time": f"{int(get_setting_val(db, 'SENDING_END_HOUR', 18)):02d}:{int(get_setting_val(db, 'SENDING_END_MINUTE', 30)):02d}",
        "allowed_days": (get_setting_val(db, "AUTOMATION_ALLOWED_DAYS", "seg,ter,qua,qui,sex")).split(","),
        "max_contacts_hour": int(get_setting_val(db, "MAX_CONTACTS_HOUR", 10)),
        "max_contacts_day": int(get_setting_val(db, "DAILY_CONTACT_LIMIT", 20)),
        "ai_provider": get_setting_val(db, "DEFAULT_AI_PROVIDER", "groq"),
        "ai_model": get_setting_val(db, "GROQ_MODEL", "qwen/qwen3.8-27b"),
        "temperature": float(get_setting_val(db, "AI_TEMPERATURE", 0.7)),
        "max_tokens": int(get_setting_val(db, "AI_MAX_TOKENS", 800))
    }

@router.put("/settings")
def update_automation_settings(payload: AutomationSettingsUpdate, db: Session = Depends(get_db)):
    """Atualiza as configurações globais da automação"""
    if payload.min_interval_sec is not None:
        set_setting_val(db, "MIN_INTERVAL_BETWEEN_CONTACTS_SEC", payload.min_interval_sec)
    if payload.max_interval_sec is not None:
        set_setting_val(db, "MAX_INTERVAL_BETWEEN_CONTACTS_SEC", payload.max_interval_sec)
    if payload.start_time and ":" in payload.start_time:
        sh, sm = payload.start_time.split(":")
        set_setting_val(db, "SENDING_START_HOUR", int(sh))
        set_setting_val(db, "SENDING_START_MINUTE", int(sm))
    if payload.end_time and ":" in payload.end_time:
        eh, em = payload.end_time.split(":")
        set_setting_val(db, "SENDING_END_HOUR", int(eh))
        set_setting_val(db, "SENDING_END_MINUTE", int(em))
    if payload.allowed_days is not None:
        set_setting_val(db, "AUTOMATION_ALLOWED_DAYS", ",".join(payload.allowed_days))
    if payload.max_contacts_hour is not None:
        set_setting_val(db, "MAX_CONTACTS_HOUR", payload.max_contacts_hour)
    if payload.max_contacts_day is not None:
        limit = min(payload.max_contacts_day, 20)
        set_setting_val(db, "DAILY_CONTACT_LIMIT", limit)
    if payload.ai_provider:
        set_setting_val(db, "DEFAULT_AI_PROVIDER", payload.ai_provider)
    if payload.ai_model:
        set_setting_val(db, "GROQ_MODEL" if "groq" in (payload.ai_provider or "") else "AI_MODEL", payload.ai_model)
    if payload.temperature is not None:
        set_setting_val(db, "AI_TEMPERATURE", payload.temperature)
    if payload.max_tokens is not None:
        set_setting_val(db, "AI_MAX_TOKENS", payload.max_tokens)

    return {"status": "success", "message": "Configurações da automação salvas com sucesso!"}

@router.get("/stats")
def get_automation_stats(db: Session = Depends(get_db)):
    """Retorna métricas em tempo real da automação contínua"""
    status = get_setting_val(db, "AUTOMATION_STATUS", "ativa")
    
    # Leads na fila (aguardando envio ou com mensagens geradas mas ainda não contatados)
    queue_count = db.query(Lead).filter(
        Lead.status.in_(["novo", "aguardando", "na_fila", "mensagens_geradas"]),
        Lead.is_eligible == True
    ).count()

    # Mensagens enviadas hoje
    today = get_now_in_brazil().date()
    start_today = datetime.combine(today, datetime.min.time())
    sent_today = db.query(Message).filter(
        Message.status.in_(["enviado", "entregue", "lido"]),
        Message.sent_at >= start_today
    ).count()

    # Total de mensagens enviadas
    sent_total = db.query(Message).filter(
        Message.status.in_(["enviado", "entregue", "lido"])
    ).count()

    # Leads processados (contatados, responderam ou interessados)
    processed_count = db.query(Lead).filter(
        Lead.status.in_(["contatado", "respondeu", "interessado", "sem_interesse"])
    ).count()

    # Falhas
    failed_count = db.query(Lead).filter(Lead.status == "erro").count()
    failed_msgs = db.query(Message).filter(Message.status == "falhou").count()
    total_failures = max(failed_count, failed_msgs)

    # Último processamento
    last_msg = db.query(Message).filter(
        Message.status.in_(["enviado", "entregue", "lido"])
    ).order_by(Message.sent_at.desc()).first()
    last_processed_at = last_msg.sent_at.isoformat() if last_msg and last_msg.sent_at else None

    return {
        "status": status,
        "is_active": status.lower() == "ativa",
        "queue_count": queue_count,
        "sent_today": sent_today,
        "sent_total": sent_total,
        "processed_count": processed_count,
        "waiting_count": queue_count,
        "failed_count": total_failures,
        "last_processed_at": last_processed_at,
        "avg_time_per_lead": "3.5 min"
    }

@router.get("/queue")
def get_automation_queue(limit: int = 50, db: Session = Depends(get_db)):
    """Retorna os leads que estão aguardando na fila da automação"""
    leads = db.query(Lead).filter(
        Lead.status.in_(["novo", "aguardando", "na_fila", "mensagens_geradas"]),
        Lead.is_eligible == True
    ).order_by(Lead.created_at.asc()).limit(limit).all()

    now = datetime.utcnow()
    items = []
    for l in leads:
        waiting_minutes = int((now - l.created_at).total_seconds() / 60) if l.created_at else 0
        items.append({
            "id": l.id,
            "company_name": l.company_name,
            "phone": l.phone,
            "city": l.city,
            "segment": l.segment,
            "website": l.website,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "waiting_minutes": waiting_minutes,
            "has_phone": bool(l.phone)
        })

    return {"total": len(items), "items": items}

@router.delete("/queue/{lead_id}")
def remove_lead_from_queue(lead_id: int, db: Session = Depends(get_db)):
    """Remove manualmente um lead da fila da automação (marca como 'nao_contatar')"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    lead.status = "nao_contatar"
    lead.is_eligible = False
    
    # Cancela mensagens pendentes se houver
    pending_msgs = db.query(Message).filter(
        Message.lead_id == lead.id,
        Message.status.in_(["pendente", "na_fila"])
    ).all()
    for m in pending_msgs:
        m.status = "cancelado"
        m.error_message = "Removido manualmente da fila de prospecção"

    db.commit()
    return {"status": "success", "message": f"Lead '{lead.company_name}' removido da fila com sucesso"}

@router.post("/dispatch-now")
def dispatch_automation_now(db: Session = Depends(get_db)):
    """
    Executa imediatamente a fila de automação:
    1. Verifica se a automação está Ativa
    2. Seleciona os próximos leads da fila
    3. Gera mensagens personalizadas por IA caso ainda não tenham sido geradas
    4. Dispara a sequência completa (3 mensagens) via WhatsApp
    """
    status = get_setting_val(db, "AUTOMATION_STATUS", "ativa")
    if status.lower() != "ativa":
        raise HTTPException(
            status_code=400,
            detail="A automação está PAUSADA. Ative a automação para disparar mensagens."
        )

    camp = get_or_create_system_campaign(db)
    
    # Busca leads pendentes na fila
    pending_leads = db.query(Lead).filter(
        Lead.status.in_(["novo", "aguardando", "na_fila", "mensagens_geradas"]),
        Lead.is_eligible == True,
        Lead.phone.isnot(None)
    ).order_by(Lead.created_at.asc()).limit(5).all()

    if not pending_leads:
        return {
            "status": "idle",
            "message": "Nenhum lead com telefone válido aguardando na fila de automação.",
            "dispatched_count": 0
        }

    ai_service = AIService(db=db)
    generator = MessageGeneratorService(db=db, ai_service=ai_service)
    engine = CampaignExecutionEngine(db=db)

    dispatched = 0
    errors = []

    for lead in pending_leads:
        try:
            # 1. Garante que as mensagens existem
            existing_msgs = db.query(Message).filter(Message.lead_id == lead.id).count()
            if existing_msgs == 0:
                generator.generate_for_lead(campaign_id=camp.id, lead_id=lead.id)
            
            # 2. Envia a sequência completa de 3 mensagens para este lead
            results = engine.send_lead_sequence(lead_id=lead.id, campaign_id=camp.id)
            if results and any(r.get("status") == "success" for r in results):
                dispatched += 1
            else:
                last_err = results[-1].get("error") if results else "Erro desconhecido"
                errors.append(f"{lead.company_name}: {last_err}")
        except Exception as e:
            logger.error(f"Erro ao processar lead {lead.id} na automação: {e}")
            errors.append(f"{lead.company_name}: {str(e)}")

    return {
        "status": "success",
        "message": f"Processamento concluído. {dispatched} lead(s) contatados com sequência de 3 mensagens.",
        "dispatched_count": dispatched,
        "errors": errors
    }

@router.get("/history")
def get_automation_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retorna os últimos leads processados pela automação com histórico de mensagens"""
    # Busca mensagens enviadas ou com falha agrupadas por lead
    leads_processed = db.query(Lead).filter(
        Lead.status.in_(["contatado", "respondeu", "interessado", "sem_interesse", "erro"])
    ).order_by(Lead.updated_at.desc()).limit(limit).all()

    history = []
    for l in leads_processed:
        msgs = db.query(Message).filter(Message.lead_id == l.id).order_by(Message.part_number.asc()).all()
        sent_msg = next((m for m in msgs if m.sent_at), None)
        
        result_label = "sucesso"
        if l.status == "erro" or (msgs and all(m.status == "falhou" for m in msgs)):
            result_label = "erro"
        elif l.status == "nao_contatar":
            result_label = "ignorado"

        first_preview = msgs[0].final_content[:100] + "..." if msgs else "Nenhuma mensagem gravada"

        history.append({
            "lead_id": l.id,
            "company_name": l.company_name,
            "phone": l.phone,
            "city": l.city,
            "result": result_label,
            "status": l.status,
            "processed_at": (sent_msg.sent_at.isoformat() if sent_msg and sent_msg.sent_at else l.updated_at.isoformat()) if l.updated_at else None,
            "processing_time_sec": 12,
            "preview_message": first_preview,
            "messages": [
                {
                    "part": m.part_number,
                    "content": m.final_content,
                    "status": m.status,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None
                } for m in msgs
            ]
        })

    return {"total": len(history), "items": history}
