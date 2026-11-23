from datetime import datetime, timedelta
from app.services.evolution.webhook_processor import EvolutionWebhookProcessor
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.campaign_lead import CampaignLead
from app.models.message import Message
from app.models.suppression_list import SuppressionList
from app.models.webhook_event import WebhookEvent

def test_webhook_idempotency(db_session):
    processor = EvolutionWebhookProcessor(db=db_session)
    event_id = "EVT_TEST_123456"
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"id": event_id, "fromMe": False, "remoteJid": "5516999991111@s.whatsapp.net"},
            "message": {"conversation": "Olá Carlos, tenho interesse!"}
        }
    }

    # 1ª execução
    success1, msg1 = processor.process_event(payload)
    assert success1 is True
    assert "sucesso" in msg1

    # 2ª execução com mesmo ID
    success2, msg2 = processor.process_event(payload)
    assert success2 is True
    assert "duplicado" in msg2

def test_webhook_incoming_cancels_future_sequence_messages(db_session):
    processor = EvolutionWebhookProcessor(db=db_session)
    phone = "+5516998887777"

    # Cria lead, campanha e mensagens pendentes (partes 2 e 3)
    lead = Lead(company_name="Empresa Teste", phone=phone, status="contatado", is_eligible=True)
    campaign = Campaign(name="Campanha Teste", status="ativa")
    db_session.add_all([lead, campaign])
    db_session.commit()

    msg1 = Message(campaign_id=campaign.id, lead_id=lead.id, part_number=1, original_content="msg 1", final_content="msg 1", status="enviado")
    msg2 = Message(campaign_id=campaign.id, lead_id=lead.id, part_number=2, original_content="msg 2", final_content="msg 2", status="pendente")
    msg3 = Message(campaign_id=campaign.id, lead_id=lead.id, part_number=3, original_content="msg 3", final_content="msg 3", status="pendente")
    db_session.add_all([msg1, msg2, msg3])
    db_session.commit()

    # Recebe resposta do lead
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"id": "EVT_REPLY_999", "fromMe": False, "remoteJid": "5516998887777@s.whatsapp.net"},
            "message": {"conversation": "Sim, podemos conversar amanhã!"}
        }
    }

    processor.process_event(payload)

    db_session.refresh(lead)
    db_session.refresh(msg2)
    db_session.refresh(msg3)

    assert lead.status == "respondeu"
    assert msg2.status == "cancelado"
    assert msg3.status == "cancelado"
    assert "lead respondeu" in msg2.error_message

def test_webhook_opt_out_stop_keyword_adds_to_suppression_list(db_session):
    processor = EvolutionWebhookProcessor(db=db_session)
    phone = "+5516991112222"

    lead = Lead(company_name="Consultório X", phone=phone, status="contatado", is_eligible=True)
    db_session.add(lead)
    db_session.commit()

    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {"id": "EVT_OPTOUT_888", "fromMe": False, "remoteJid": "5516991112222@s.whatsapp.net"},
            "message": {"conversation": "Favor parar de enviar mensagens"}
        }
    }

    processor.process_event(payload)

    db_session.refresh(lead)
    assert lead.status == "nao_contatar"
    assert lead.is_eligible is False

    supp = db_session.query(SuppressionList).filter(SuppressionList.phone == phone).first()
    assert supp is not None
    assert supp.reason == "opt_out"
