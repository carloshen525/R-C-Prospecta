from app.celery_app import celery
from app.database import SessionLocal
from app.services.campaigns.engine import CampaignExecutionEngine
from app.core.logging import logger

@celery.task(name="app.tasks.campaign_tasks.dispatch_scheduled_campaign_messages")
def dispatch_scheduled_campaign_messages():
    """
    Tarefa periódica executada a cada 1 minuto pelo Celery Beat.
    Verifica mensagens pendentes, respeitando a janela das 07:00 às 18:30 e o limite diário de 30 contatos.
    """
    db = SessionLocal()
    try:
        engine = CampaignExecutionEngine(db=db)
        results = engine.dispatch_next_batch(max_messages=10)
        if results:
            logger.info(f"Fila processou {len(results)} mensagens no ciclo atual.")
        return {"processed": len(results), "details": results}
    except Exception as e:
        logger.error(f"Erro ao disparar mensagens agendadas: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery.task(name="app.tasks.campaign_tasks.dispatch_single_message_now")
def dispatch_single_message_now(message_id: int):
    """Envia uma mensagem pontual sob demanda"""
    db = SessionLocal()
    try:
        engine = CampaignExecutionEngine(db=db)
        result = engine.send_single_message(message_id)
        return result
    finally:
        db.close()
