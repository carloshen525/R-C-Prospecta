from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.models.conversation import Conversation, ConversationEvent
from app.models.lead import Lead
from app.models.message import Message
from app.models.suppression_list import SuppressionList
from app.schemas.conversation import ConversationResponse, ConversationEventCreate, ConversationStatusUpdate
from app.services.evolution.client import EvolutionAPIClient
from app.core.logging import logger

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_conversations(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Conversation).join(Lead)
    if status:
        query = query.filter(Conversation.status == status)

    conversations = query.order_by(Conversation.last_message_at.desc()).all()
    results = []
    for c in conversations:
        results.append({
            "id": c.id,
            "lead_id": c.lead_id,
            "company_name": c.lead.company_name if c.lead else None,
            "phone": c.phone,
            "status": c.status,
            "lead_status": c.lead.status if c.lead else None,
            "segment": c.lead.segment if c.lead else None,
            "city": c.lead.city if c.lead else None,
            "website": c.lead.website if c.lead else None,
            "last_message_at": c.last_message_at,
            "unread_count": c.unread_count
        })
    return results

@router.get("/{conversation_id}")
def get_conversation_detail(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    # Marca mensagens como lidas
    conv.unread_count = 0
    db.commit()

    events = db.query(ConversationEvent).filter(
        ConversationEvent.conversation_id == conv.id
    ).order_by(ConversationEvent.created_at.asc()).all()

    lead_data = None
    if conv.lead:
        lead_data = {
            "id": conv.lead.id,
            "company_name": conv.lead.company_name,
            "phone": conv.lead.phone,
            "segment": conv.lead.segment,
            "city": conv.lead.city,
            "state": conv.lead.state,
            "website": conv.lead.website,
            "rating": conv.lead.rating,
            "status": conv.lead.status,
            "website_data": conv.lead.website_data,
            "notes": conv.lead.notes
        }

    return {
        "conversation": conv,
        "lead": lead_data,
        "events": events
    }

@router.post("/{conversation_id}/reply")
def send_manual_reply(
    conversation_id: int,
    reply_in: ConversationEventCreate,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    client = EvolutionAPIClient()
    evo_res = client.send_text_message(phone=conv.phone, text=reply_in.message_content)

    evo_id = (
        evo_res.get("key", {}).get("id") or
        evo_res.get("messageId") or
        evo_res.get("id")
    )

    event = ConversationEvent(
        conversation_id=conv.id,
        direction="outgoing",
        message_content=reply_in.message_content,
        evolution_message_id=evo_id,
        raw_payload=evo_res,
        status="sent"
    )
    db.add(event)
    conv.last_message_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "event_id": event.id, "evolution_id": evo_id}

@router.put("/{conversation_id}/status")
def update_conversation_status(
    conversation_id: int,
    status_in: ConversationStatusUpdate,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    conv.status = status_in.status
    if conv.lead:
        if status_in.status == "interessado":
            conv.lead.status = "interessado"
        elif status_in.status == "sem_interesse":
            conv.lead.status = "sem_interesse"
        elif status_in.status == "finalizada":
            conv.lead.status = "contatado"

    db.commit()
    return {"status": "success", "new_status": conv.status}

@router.post("/{conversation_id}/opt-out")
def mark_opt_out(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")

    conv.status = "finalizada"
    if conv.lead:
        conv.lead.status = "nao_contatar"
        conv.lead.is_eligible = False

        supp = db.query(SuppressionList).filter(SuppressionList.phone == conv.phone).first()
        if not supp:
            db.add(SuppressionList(phone=conv.phone, reason="opt_out", notes="Marcado manualmente via CRM"))

        # Cancela mensagens agendadas
        pending = db.query(Message).filter(
            Message.lead_id == conv.lead.id,
            Message.status.in_(["pendente", "na_fila"])
        ).all()
        for p in pending:
            p.status = "cancelado"
            p.error_message = "Opt-out solicitado"

    db.commit()
    return {"status": "success", "message": "Lead adicionado à lista de supressão e envios cancelados"}
