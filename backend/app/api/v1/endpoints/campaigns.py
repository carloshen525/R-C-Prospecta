from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from app.database import get_db, SessionLocal
from app.models.campaign import Campaign
from app.models.campaign_lead import CampaignLead
from app.models.lead import Lead
from app.models.message import Message
from app.models.generated_sequence import GeneratedSequence
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse, CampaignActionRequest
from app.schemas.message import MessageResponse, MessageUpdate
from app.services.ai_providers.ai_service import AIService
from app.services.message_generator.generator import MessageGeneratorService
from app.core.logging import logger

router = APIRouter()

def run_generate_messages_background(campaign_id: int):
    db = SessionLocal()
    try:
        from app.tasks.ai_tasks import generate_messages_for_campaign_leads
        generate_messages_for_campaign_leads(None, campaign_id)
    except Exception as e:
        logger.error(f"Erro ao gerar mensagens em background: {e}")
    finally:
        db.close()

def run_dispatch_background(campaign_id: int):
    db = SessionLocal()
    try:
        from app.services.campaigns.engine import CampaignExecutionEngine
        engine = CampaignExecutionEngine(db=db)
        engine.dispatch_next_batch(max_messages=5)
    except Exception as e:
        logger.error(f"Erro no background dispatch da campanha {campaign_id}: {e}")
    finally:
        db.close()

@router.get("", response_model=List[CampaignResponse])
def list_campaigns(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()
    results = []
    for c in campaigns:
        total_leads = db.query(CampaignLead).filter(CampaignLead.campaign_id == c.id).count()
        leads_processed = db.query(CampaignLead).filter(CampaignLead.campaign_id == c.id, CampaignLead.status != "aguardando").count()
        messages_gen = db.query(Message).filter(Message.campaign_id == c.id).count()
        contacts_sent = db.query(Message).filter(Message.campaign_id == c.id, Message.status.in_(["enviado", "entregue", "lido"])).count()
        responses = db.query(CampaignLead).filter(CampaignLead.campaign_id == c.id, CampaignLead.status == "respondeu").count()
        interested = db.query(CampaignLead).join(Lead).filter(CampaignLead.campaign_id == c.id, Lead.status == "interessado").count()

        resp = CampaignResponse.from_orm(c)
        resp.total_leads = total_leads
        resp.leads_processed = leads_processed
        resp.messages_generated = messages_gen
        resp.contacts_sent = contacts_sent
        resp.responses_count = responses
        resp.interested_count = interested
        results.append(resp)

    return results

@router.post("", response_model=CampaignResponse)
def create_campaign(camp_in: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(
        name=camp_in.name,
        description=camp_in.description,
        segment=camp_in.segment,
        location=camp_in.location,
        ai_provider=camp_in.ai_provider,
        ai_model=camp_in.ai_model,
        custom_prompt=camp_in.custom_prompt,
        daily_limit=min(camp_in.daily_limit, 30), # Cap at 30
        interval_min_seconds=camp_in.interval_min_seconds,
        interval_max_seconds=camp_in.interval_max_seconds,
        followup_1_delay_hours=camp_in.followup_1_delay_hours,
        followup_2_delay_hours=camp_in.followup_2_delay_hours,
        status="rascunho"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Associa leads selecionados
    if camp_in.lead_ids:
        for lid in camp_in.lead_ids:
            assoc = CampaignLead(campaign_id=campaign.id, lead_id=lid, status="aguardando")
            db.add(assoc)
        db.commit()

    resp = CampaignResponse.from_orm(campaign)
    resp.total_leads = len(camp_in.lead_ids or [])
    return resp

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    total_leads = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign.id).count()
    leads_processed = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign.id, CampaignLead.status != "aguardando").count()
    messages_gen = db.query(Message).filter(Message.campaign_id == campaign.id).count()
    contacts_sent = db.query(Message).filter(Message.campaign_id == campaign.id, Message.status.in_(["enviado", "entregue", "lido"])).count()
    responses = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign.id, CampaignLead.status == "respondeu").count()
    interested = db.query(CampaignLead).join(Lead).filter(CampaignLead.campaign_id == campaign.id, Lead.status == "interessado").count()

    resp = CampaignResponse.from_orm(campaign)
    resp.total_leads = total_leads
    resp.leads_processed = leads_processed
    resp.messages_generated = messages_gen
    resp.contacts_sent = contacts_sent
    resp.responses_count = responses
    resp.interested_count = interested
    return resp

@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: int, camp_in: CampaignUpdate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    update_data = camp_in.dict(exclude_unset=True)
    if "daily_limit" in update_data and update_data["daily_limit"]:
        update_data["daily_limit"] = min(update_data["daily_limit"], 30)

    for field, val in update_data.items():
        setattr(campaign, field, val)

    db.commit()
    db.refresh(campaign)
    return CampaignResponse.from_orm(campaign)

@router.post("/{campaign_id}/action")
def campaign_action(
    campaign_id: int,
    action_data: CampaignActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    act = action_data.action.lower()
    total_leads = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign.id).count()

    if act == "start":
        if total_leads == 0:
            raise HTTPException(
                status_code=400,
                detail=f"A campanha '{campaign.name}' possui 0 leads associados. Adicione leads na aba 'Leads' ou 'Extrator de Leads' antes de iniciar."
            )
        campaign.status = "ativa"
        db.commit()

        # Verifica se há leads que precisam de mensagens geradas
        pending_gen = db.query(CampaignLead).filter(
            CampaignLead.campaign_id == campaign.id,
            CampaignLead.status == "aguardando"
        ).count()
        if pending_gen > 0:
            background_tasks.add_task(run_generate_messages_background, campaign.id)

        # Dispara mensagens prontas em background
        background_tasks.add_task(run_dispatch_background, campaign.id)

    elif act == "pause":
        campaign.status = "pausada"
        db.commit()
    elif act == "resume":
        campaign.status = "ativa"
        db.commit()
        background_tasks.add_task(run_dispatch_background, campaign.id)
    elif act == "stop":
        campaign.status = "concluida"
        db.commit()
    else:
        raise HTTPException(status_code=400, detail=f"Ação desconhecida: {act}")

    return {"status": "success", "campaign_status": campaign.status}

@router.post("/{campaign_id}/dispatch")
def dispatch_campaign_now(campaign_id: int, db: Session = Depends(get_db)):
    """Dispara mensagens pendentes agora respeitando as regras de compliance"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    total_leads = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign.id).count()
    if total_leads == 0:
        raise HTTPException(
            status_code=400,
            detail=f"A campanha '{campaign.name}' possui 0 leads associados. Adicione leads antes de disparar."
        )

    # Se há leads aguardando mensagens da IA, gera primeiro
    pending_gen = db.query(CampaignLead).filter(
        CampaignLead.campaign_id == campaign.id,
        CampaignLead.status == "aguardando"
    ).all()
    if pending_gen:
        ai_service = AIService(db=db)
        generator = MessageGeneratorService(db=db, ai_service=ai_service)
        for cl in pending_gen:
            try:
                cl.status = "gerando_mensagens"
                db.commit()
                generator.generate_for_lead(campaign_id=campaign.id, lead_id=cl.lead_id)
                cl.status = "pronto_para_envio"
                db.commit()
            except Exception as e:
                cl.status = "erro"
                cl.error_message = str(e)
                db.commit()

    if campaign.status != "ativa":
        campaign.status = "ativa"
        db.commit()

    from app.services.campaigns.engine import CampaignExecutionEngine
    engine = CampaignExecutionEngine(db=db)
    results = engine.dispatch_next_batch(max_messages=5)
    return {
        "status": "success",
        "campaign_id": campaign.id,
        "dispatched_count": len(results),
        "details": results
    }

@router.post("/{campaign_id}/generate-messages")
def trigger_message_generation(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    campaign.status = "preparando"
    db.commit()

    try:
        from app.tasks.ai_tasks import generate_messages_for_campaign_leads
        generate_messages_for_campaign_leads.delay(campaign_id)
    except Exception:
        background_tasks.add_task(run_generate_messages_background, campaign_id)

    return {"status": "success", "message": "Geração de mensagens iniciada em segundo plano"}

@router.get("/{campaign_id}/leads")
def get_campaign_leads(campaign_id: int, db: Session = Depends(get_db)):
    assocs = db.query(CampaignLead).filter(CampaignLead.campaign_id == campaign_id).all()
    leads_data = []
    for a in assocs:
        leads_data.append({
            "campaign_lead_id": a.id,
            "status": a.status,
            "error_message": a.error_message,
            "lead": a.lead
        })
    return leads_data

@router.get("/{campaign_id}/messages", response_model=List[MessageResponse])
def get_campaign_messages(campaign_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.campaign_id == campaign_id).order_by(Message.id.desc()).all()
    return messages

@router.put("/messages/{message_id}", response_model=MessageResponse)
def update_message_content(message_id: int, msg_in: MessageUpdate, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    if msg.status in ("enviado", "entregue", "lido"):
        raise HTTPException(status_code=400, detail="Não é possível editar uma mensagem que já foi enviada")

    msg.final_content = msg_in.final_content
    db.commit()
    db.refresh(msg)
    return msg
