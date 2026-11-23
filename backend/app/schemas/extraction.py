from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExtractionJobCreate(BaseModel):
    segment: str = Field(..., description="Segmento ou nicho (ex: Clínicas Odontológicas)")
    city: str = Field(..., description="Cidade (ex: Ribeirão Preto)")
    state: str = Field(..., description="Estado (ex: SP)")
    country: str = "Brasil"
    desired_qty: int = Field(default=50, ge=1, le=500)
    has_phone_filter: bool = True
    has_website_filter: bool = False
    source: Optional[str] = Field(default="google_scraper", description="Motor: google_scraper, google_places, openstreetmap ou auto")
    auto_import: Optional[bool] = False
    campaign_id: Optional[int] = None

class ExtractionImportRequest(BaseModel):
    selected_indices: List[int] = Field(..., description="Índices dos leads selecionados para importação")
    campaign_id: Optional[int] = None

class ExtractionJobResponse(BaseModel):
    id: int
    user_id: Optional[int]
    segment: str
    city: str
    state: str
    country: str
    desired_qty: int
    has_phone_filter: bool
    has_website_filter: bool
    source: Optional[str] = "google_scraper"
    auto_import: Optional[bool] = False
    campaign_id: Optional[int]
    status: str
    found_count: int
    processed_count: int
    saved_count: int
    duplicate_count: int
    error_count: int
    execution_time_seconds: float
    error_log: Optional[str]
    extracted_items: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
