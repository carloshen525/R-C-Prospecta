from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.setting import TestConnectionRequest
from app.services.ai_providers.ai_service import AIService
from app.core.logging import logger

router = APIRouter()

@router.post("/test-connection")
def test_ai_connection(req: TestConnectionRequest):
    """Testa a conectividade com OpenAI, Groq ou Google Gemini"""
    service = AIService()
    success, message = service.test_provider(req.provider, api_key=req.api_key)
    return {
        "provider": req.provider,
        "success": success,
        "message": message
    }
