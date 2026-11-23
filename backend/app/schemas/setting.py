from pydantic import BaseModel
from typing import Optional, Dict, Any

class SettingUpdate(BaseModel):
    settings: Dict[str, Any]

class SettingsGroupResponse(BaseModel):
    whatsapp: Dict[str, Any]
    ai: Dict[str, Any]
    sending: Dict[str, Any]

class TestConnectionRequest(BaseModel):
    provider: Optional[str] = "evolution" # openai, groq, gemini, evolution
    api_key: Optional[str] = None
    url: Optional[str] = None
    instance: Optional[str] = None
