from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingUpdate
from app.config import settings

router = APIRouter()

def mask_secret(value: str) -> str:
    if not value or len(value) < 8:
        return "••••••••" if value else ""
    return f"{value[:3]}••••{value[-4:]}"

@router.get("")
def get_all_settings(db: Session = Depends(get_db)):
    db_settings = {s.key: s.value for s in db.query(Setting).all()}

    evo_url = db_settings.get("EVOLUTION_API_URL", settings.EVOLUTION_API_URL or "")
    evo_key = db_settings.get("EVOLUTION_API_KEY", settings.EVOLUTION_API_KEY or "")
    evo_inst = db_settings.get("EVOLUTION_INSTANCE_NAME", settings.EVOLUTION_INSTANCE_NAME or "")

    openai_key = db_settings.get("OPENAI_API_KEY", settings.OPENAI_API_KEY or "")
    groq_key = db_settings.get("GROQ_API_KEY", settings.GROQ_API_KEY or "")
    gemini_key = db_settings.get("GEMINI_API_KEY", settings.GEMINI_API_KEY or "")
    google_key = db_settings.get("GOOGLE_MAPS_API_KEY", settings.GOOGLE_MAPS_API_KEY or "")

    return {
        "google_maps": {
            "api_key_masked": mask_secret(google_key),
            "is_configured": bool(google_key)
        },
        "whatsapp": {
            "evolution_url": evo_url,
            "evolution_key_masked": mask_secret(evo_key),
            "evolution_instance": evo_inst,
            "is_configured": bool(evo_url and evo_key and evo_inst)
        },
        "ai": {
            "default_provider": db_settings.get("DEFAULT_AI_PROVIDER", settings.DEFAULT_AI_PROVIDER),
            "fallback_provider": db_settings.get("FALLBACK_AI_PROVIDER", settings.FALLBACK_AI_PROVIDER),
            "openai_configured": bool(openai_key),
            "openai_key_masked": mask_secret(openai_key),
            "openai_model": db_settings.get("OPENAI_MODEL", settings.OPENAI_MODEL),
            "groq_configured": bool(groq_key),
            "groq_key_masked": mask_secret(groq_key),
            "groq_model": db_settings.get("GROQ_MODEL", settings.GROQ_MODEL),
            "gemini_configured": bool(gemini_key),
            "gemini_key_masked": mask_secret(gemini_key),
            "gemini_model": db_settings.get("GEMINI_MODEL", settings.GEMINI_MODEL),
        },
        "sending": {
            "daily_contact_limit": int(db_settings.get("DAILY_CONTACT_LIMIT", settings.DAILY_CONTACT_LIMIT)),
            "start_time": f"{int(db_settings.get('SENDING_START_HOUR', settings.SENDING_START_HOUR)):02d}:{int(db_settings.get('SENDING_START_MINUTE', settings.SENDING_START_MINUTE)):02d}",
            "end_time": f"{int(db_settings.get('SENDING_END_HOUR', settings.SENDING_END_HOUR)):02d}:{int(db_settings.get('SENDING_END_MINUTE', settings.SENDING_END_MINUTE)):02d}",
            "timezone": settings.TIMEZONE,
            "min_interval_sec": int(db_settings.get("MIN_INTERVAL_BETWEEN_CONTACTS_SEC", settings.MIN_INTERVAL_BETWEEN_CONTACTS_SEC)),
            "max_interval_sec": int(db_settings.get("MAX_INTERVAL_BETWEEN_CONTACTS_SEC", settings.MAX_INTERVAL_BETWEEN_CONTACTS_SEC)),
            "followup_1_delay_hours": int(db_settings.get("FOLLOWUP_1_DELAY_HOURS", settings.FOLLOWUP_1_DELAY_HOURS)),
            "followup_2_delay_hours": int(db_settings.get("FOLLOWUP_2_DELAY_HOURS", settings.FOLLOWUP_2_DELAY_HOURS)),
        }
    }

@router.post("/test-google-places")
def test_google_places_api(payload: dict, db: Session = Depends(get_db)):
    key = payload.get("api_key")
    if not key:
        setting_rec = db.query(Setting).filter(Setting.key == "GOOGLE_MAPS_API_KEY").first()
        if setting_rec and setting_rec.value:
            key = setting_rec.value
        elif getattr(settings, "GOOGLE_MAPS_API_KEY", None):
            key = settings.GOOGLE_MAPS_API_KEY

    from app.services.lead_acquisition.google_places_adapter import GooglePlacesAdapter
    adapter = GooglePlacesAdapter(api_key=key)
    success, msg = adapter.test_connection()
    return {"success": success, "message": msg}

@router.put("")
def update_settings(payload: SettingUpdate, db: Session = Depends(get_db)):
    for k, v in payload.settings.items():
        if v is None:
            continue
        
        # Validação do limite diário
        if k == "DAILY_CONTACT_LIMIT":
            val_int = int(v)
            if val_int > 20:
                raise HTTPException(status_code=400, detail="O limite diário de contatos não pode exceder 20")

        setting_rec = db.query(Setting).filter(Setting.key == k).first()
        if not setting_rec:
            setting_rec = Setting(key=k, value=str(v), category="general")
            db.add(setting_rec)
        else:
            setting_rec.value = str(v)

    db.commit()
    return {"status": "success", "message": "Configurações salvas com sucesso"}
