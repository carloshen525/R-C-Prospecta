from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    dashboard,
    extraction,
    leads,
    campaigns,
    automation,
    ai_settings,
    evolution,
    conversations,
    reports,
    settings
)
from app.api.v1.webhooks import evolution_webhook

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(extraction.router, prefix="/extraction", tags=["Extrator de Leads"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(automation.router, prefix="/automation", tags=["Automação de Prospecção"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campanhas"])
api_router.include_router(ai_settings.router, prefix="/ai", tags=["Inteligência Artificial"])
api_router.include_router(evolution.router, prefix="/evolution", tags=["Evolution WhatsApp API"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversas e Atendimento"])
api_router.include_router(reports.router, prefix="/reports", tags=["Relatórios"])
api_router.include_router(settings.router, prefix="/settings", tags=["Configurações"])
api_router.include_router(evolution_webhook.router, prefix="/webhooks/evolution", tags=["Webhooks"])
