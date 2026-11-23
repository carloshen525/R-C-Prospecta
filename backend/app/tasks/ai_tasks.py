from app.celery_app import celery
from app.database import SessionLocal
from app.services.ai_providers.ai_service import AIService
from app.services.message_generator.generator import MessageGeneratorService
from app.models.campaign import Campaign
from app.models.campaign_lead import CampaignLead
from app.models.message import Message
from app.core.logging import logger

@celery.task(name="app.tasks.ai_tasks.generate_messages_for_campaign_leads", bind=True)
def generate_messages_for_campaign_leads(self, campaign_id: int):
    logger.info(f"Iniciando geração de mensagens IA para campanha {campaign_id}")
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"status": "error", "message": "Campanha não encontrada"}

        ai_service = AIService(db=db)
        msg_generator = MessageGeneratorService(db=db, ai_service=ai_service)

        # Busca leads da campanha que ainda não possuem mensagens geradas
        associations = db.query(CampaignLead).filter(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.status == "aguardando"
        ).all()

        count = 0
        for assoc in associations:
            try:
                # Verifica se já não tem mensagens criadas para evitar duplicatas
                existing_msg = db.query(Message).filter(
                    Message.campaign_id == campaign_id,
                    Message.lead_id == assoc.lead_id
                ).first()

                if not existing_msg:
                    assoc.status = "gerando_mensagens"
                    db.commit()
                    
                    msg_generator.generate_for_lead(campaign_id=campaign_id, lead_id=assoc.lead_id)
                    assoc.status = "pronto_para_envio"
                    count += 1
                else:
                    assoc.status = "pronto_para_envio"
                db.commit()
            except Exception as item_err:
                logger.error(f"Erro ao gerar mensagens para lead {assoc.lead_id}: {item_err}")
                assoc.status = "erro"
                assoc.error_message = str(item_err)
                db.commit()

        # Atualiza status da campanha
        if campaign.status == "preparando":
            campaign.status = "aguardando_inicio"
            db.commit()

        return {"status": "success", "processed_leads": count}
    finally:
        db.close()
