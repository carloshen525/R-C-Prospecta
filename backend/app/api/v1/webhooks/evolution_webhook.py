from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from app.database import get_db
from app.services.evolution.webhook_processor import EvolutionWebhookProcessor
from app.core.logging import logger

router = APIRouter()

@router.post("")
async def receive_evolution_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Recebe eventos em tempo real da Evolution API.
    Processa mensagens recebidas, atualizações de status e realiza deduplicação idempotente.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Webhook com JSON inválido: {e}")
        raise HTTPException(status_code=400, detail="Corpo da requisição deve ser JSON válido")

    processor = EvolutionWebhookProcessor(db=db)
    success, message = processor.process_event(payload)
    
    return {"status": "success" if success else "error", "message": message}
