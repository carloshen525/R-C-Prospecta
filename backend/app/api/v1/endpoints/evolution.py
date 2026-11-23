from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.setting import Setting
from app.schemas.setting import TestConnectionRequest
from app.services.evolution.client import EvolutionAPIClient
from app.core.logging import logger

router = APIRouter()

@router.post("/test-connection")
def test_evolution_connection(req: TestConnectionRequest, db: Session = Depends(get_db)):
    """Testa a conectividade com a Evolution API"""
    url = (req.url or "").strip()
    api_key = (req.api_key or "").strip()
    instance = (req.instance or "").strip()

    # Se algum campo não veio no payload, busca na tabela Setting
    if not url:
        s_url = db.query(Setting).filter(Setting.key == "EVOLUTION_API_URL").first()
        if s_url and s_url.value:
            url = s_url.value.strip()
    if not api_key:
        s_key = db.query(Setting).filter(Setting.key == "EVOLUTION_API_KEY").first()
        if s_key and s_key.value:
            api_key = s_key.value.strip()
    if not instance:
        s_inst = db.query(Setting).filter(Setting.key == "EVOLUTION_INSTANCE_NAME").first()
        if s_inst and s_inst.value:
            instance = s_inst.value.strip()

    client = EvolutionAPIClient(
        base_url=url,
        api_key=api_key,
        instance_name=instance
    )
    success, message, data = client.check_connection()
    return {
        "success": success,
        "message": message,
        "details": data
    }
