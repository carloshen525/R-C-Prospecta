from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.v1.api import api_router
from app.core.exceptions import ProspectAIException
from app.core.logging import logger
from app.models.user import User
from app.models.lead_source import LeadSource
from app.core.security import get_password_hash

import app.models
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização: cria tabelas no banco de dados
    logger.info("Inicializando Prospect AI - Criando schema no banco se necessário...")
    Base.metadata.create_all(bind=engine)

    # Garante colunas que possam faltar em bancos PostgreSQL já inicializados
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'google_scraper'"))
            conn.execute(text("ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS auto_import BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE extraction_jobs ADD COLUMN IF NOT EXISTS extracted_items JSONB"))
            conn.commit()
    except Exception as col_err:
        logger.debug(f"Verificação de colunas extraction_jobs: {col_err}")

    # Popula usuário admin padrão e fontes iniciais caso o banco esteja novo
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            default_admin = User(
                email="admin@prospectai.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Carlos Administrador",
                is_active=True,
                is_superuser=True
            )
            db.add(default_admin)
            db.commit()
            logger.info("Usuário inicial criado: admin@prospectai.com / admin123")

        # Garante fontes padrão
        if db.query(LeadSource).count() == 0:
            db.add(LeadSource(name="Google Maps", slug="google_maps", is_active=True))
            db.add(LeadSource(name="OpenStreetMap / Nominatim", slug="osm", is_active=True))
            db.commit()
    except Exception as e:
        logger.error(f"Erro no bootstrap inicial: {e}")
    finally:
        db.close()

    # Inicia tarefa em segundo plano para despacho contínuo autônomo (roda a cada 60s)
    import asyncio
    async def continuous_dispatcher_task():
        await asyncio.sleep(5)
        while True:
            try:
                from app.database import SessionLocal
                from app.services.campaigns.engine import CampaignExecutionEngine
                db_loop = SessionLocal()
                try:
                    engine_loop = CampaignExecutionEngine(db=db_loop)
                    engine_loop.dispatch_next_batch(max_messages=1)
                finally:
                    db_loop.close()
            except Exception as loop_err:
                logger.debug(f"Ciclo automático de verificação: {loop_err}")
            await asyncio.sleep(60)

    loop_task = asyncio.create_task(continuous_dispatcher_task())

    yield

    loop_task.cancel()
    logger.info("Desligando Prospect AI...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Plataforma autônoma de prospecção comercial B2B com IA e WhatsApp",
    lifespan=lifespan
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite acesso para desenvolvimento e produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler central de exceções de negócio
@app.exception_handler(ProspectAIException)
async def prospect_ai_exception_handler(request: Request, exc: ProspectAIException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.__class__.__name__, "message": exc.message, "details": exc.details}
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro 500 não tratado em {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": exc.__class__.__name__, "message": str(exc), "detail": str(exc)}
    )

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }

# Roteador de API v1
app.include_router(api_router, prefix="/api/v1")
