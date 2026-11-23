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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização: cria tabelas no banco de dados
    logger.info("Inicializando Prospect AI - Criando schema no banco se necessário...")
    Base.metadata.create_all(bind=engine)

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

    yield

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

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }

# Roteador de API v1
app.include_router(api_router, prefix="/api/v1")
