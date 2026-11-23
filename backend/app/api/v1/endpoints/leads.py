from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.lead import Lead
from app.models.campaign_lead import CampaignLead
from app.models.suppression_list import SuppressionList
from app.models.message import Message
from app.models.generated_sequence import GeneratedSequence
from app.models.conversation import Conversation
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse, LeadBulkAction, LeadListResponse
from app.services.lead_acquisition.lead_service import normalize_phone_e164, is_phone_suppressed
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.get("", response_model=LeadListResponse)
def list_leads(
    search: Optional[str] = None,
    segment: Optional[str] = None,
    city: Optional[str] = None,
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    has_phone: Optional[bool] = None,
    has_website: Optional[bool] = None,
    is_eligible: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Lead)

    if search:
        s = f"%{search}%"
        query = query.filter(or_(
            Lead.company_name.ilike(s),
            Lead.phone.ilike(s),
            Lead.city.ilike(s),
            Lead.segment.ilike(s)
        ))

    if segment:
        query = query.filter(Lead.segment.ilike(f"%{segment}%"))
    if city:
        query = query.filter(Lead.city.ilike(f"%{city}%"))
    if status:
        query = query.filter(Lead.status == status)
    if is_eligible is not None:
        query = query.filter(Lead.is_eligible == is_eligible)
    if has_phone is True:
        query = query.filter(Lead.phone != None, Lead.phone != "")
    elif has_phone is False:
        query = query.filter(or_(Lead.phone == None, Lead.phone == ""))
    if has_website is True:
        query = query.filter(Lead.website != None, Lead.website != "")
    elif has_website is False:
        query = query.filter(or_(Lead.website == None, Lead.website == ""))

    if campaign_id:
        query = query.join(CampaignLead).filter(CampaignLead.campaign_id == campaign_id)

    total = query.count()
    leads = query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()

    return LeadListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=[LeadResponse.model_validate(l) for l in leads]
    )

@router.get("/{lead_id}", response_model=Dict[str, Any])
def get_lead_details(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    # Coleta sequências e mensagens geradas
    sequences = db.query(GeneratedSequence).filter(GeneratedSequence.lead_id == lead.id).all()
    messages = db.query(Message).filter(Message.lead_id == lead.id).order_by(Message.part_number.asc()).all()
    conversation = db.query(Conversation).filter(Conversation.lead_id == lead.id).first()
    campaigns = db.query(CampaignLead).filter(CampaignLead.lead_id == lead.id).all()

    return {
        "lead": LeadResponse.model_validate(lead).model_dump(),
        "sequences": jsonable_encoder(sequences),
        "messages": jsonable_encoder(messages),
        "conversation": jsonable_encoder(conversation) if conversation else None,
        "campaigns_count": len(campaigns)
    }

@router.post("", response_model=LeadResponse)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    norm_phone = normalize_phone_e164(lead_in.phone) if lead_in.phone else None
    suppressed = is_phone_suppressed(db, norm_phone) if norm_phone else False

    lead = Lead(
        company_name=lead_in.company_name,
        phone=norm_phone,
        raw_phone=lead_in.phone,
        address=lead_in.address,
        city=lead_in.city,
        state=lead_in.state,
        country=lead_in.country or "Brasil",
        website=lead_in.website,
        category=lead_in.category,
        segment=lead_in.segment,
        rating=lead_in.rating,
        rating_count=lead_in.rating_count,
        description=lead_in.description,
        source=lead_in.source or "Manual",
        status="nao_contatar" if suppressed else (lead_in.status or "novo"),
        is_eligible=not suppressed if lead_in.is_eligible is None else lead_in.is_eligible,
        notes=lead_in.notes
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, lead_in: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    update_data = lead_in.dict(exclude_unset=True)
    if "phone" in update_data and update_data["phone"]:
        update_data["phone"] = normalize_phone_e164(update_data["phone"])

    for field, val in update_data.items():
        setattr(lead, field, val)

    db.commit()
    db.refresh(lead)
    return lead

@router.post("/bulk")
def bulk_action(action_data: LeadBulkAction, db: Session = Depends(get_db)):
    leads = db.query(Lead).filter(Lead.id.in_(action_data.lead_ids)).all()
    affected = 0

    if action_data.action == "add_to_campaign":
        if not action_data.campaign_id:
            raise HTTPException(status_code=400, detail="campaign_id obrigatório para esta ação")
        for lead in leads:
            if lead.is_eligible and lead.phone:
                exists = db.query(CampaignLead).filter(
                    CampaignLead.campaign_id == action_data.campaign_id,
                    CampaignLead.lead_id == lead.id
                ).first()
                if not exists:
                    db.add(CampaignLead(campaign_id=action_data.campaign_id, lead_id=lead.id, status="aguardando"))
                    affected += 1

    elif action_data.action == "change_status":
        if not action_data.status:
            raise HTTPException(status_code=400, detail="status obrigatório para esta ação")
        for lead in leads:
            lead.status = action_data.status
            affected += 1

    elif action_data.action == "block":
        for lead in leads:
            lead.status = "nao_contatar"
            lead.is_eligible = False
            if lead.phone:
                supp = db.query(SuppressionList).filter(SuppressionList.phone == lead.phone).first()
                if not supp:
                    db.add(SuppressionList(phone=lead.phone, reason="manual_block", notes="Bloqueado em lote"))
            affected += 1

    db.commit()
    return {"status": "success", "action": action_data.action, "affected_count": affected}
