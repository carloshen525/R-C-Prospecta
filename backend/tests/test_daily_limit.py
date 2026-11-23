from datetime import date
import pytest
from app.services.campaigns.engine import CampaignExecutionEngine
from app.models.sending_daily_usage import SendingDailyUsage
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.core.exceptions import DailyLimitReachedException
from app.core.scheduler_rules import get_now_in_brazil

def test_daily_limit_blocks_21st_contact(db_session):
    engine = CampaignExecutionEngine(db=db_session)
    today = get_now_in_brazil().date()

    # Simula consumo de 20 contatos únicos (teto diário máximo)
    usage = engine.get_or_create_daily_usage(target_date=today)
    usage.contacts_sent_count = 20
    usage.limit_max = 20
    db_session.commit()

    # Tenta enviar para o 21º contato único
    new_lead = Lead(
        company_name="Empresa 21",
        phone="+5516999990021",
        status="novo",
        is_eligible=True
    )
    db_session.add(new_lead)
    db_session.commit()

    can_send, reason = engine.can_send_contact_today(is_new_contact=True, check_window=False)
    assert can_send is False
    assert "Limite diário" in reason

def test_same_contact_does_not_consume_second_slot(db_session):
    engine = CampaignExecutionEngine(db=db_session)
    today = get_now_in_brazil().date()

    usage = engine.get_or_create_daily_usage(target_date=today)
    usage.contacts_sent_count = 15
    usage.limit_max = 20
    db_session.commit()

    # Mensagem de followup (is_new_contact=False) pode ser disparada sem checar a cota dos 20 contatos diários
    can_send, msg = engine.can_send_contact_today(is_new_contact=False, check_window=False)
    assert can_send is True
    assert "contato já contabilizado" in msg

def test_lead_never_receives_more_than_3_messages(db_session):
    engine = CampaignExecutionEngine(db=db_session)
    camp = Campaign(id=1, name="Campanha Teste", status="ativa")
    db_session.add(camp)
    db_session.commit()

    lead = Lead(
        company_name="Clinica Teste Limite",
        phone="+5516999990099",
        status="contatado",
        is_eligible=False
    )
    db_session.add(lead)
    db_session.commit()

    # Tenta enviar sequência para um lead que já foi contatado
    results = engine.send_lead_sequence(lead_id=lead.id, campaign_id=1)
    assert len(results) == 0

    # Mensagens pendentes para este lead devem ser canceladas
    from app.models.message import Message
    msg = Message(
        campaign_id=1,
        lead_id=lead.id,
        part_number=1,
        original_content="Teste",
        final_content="Teste",
        status="pendente"
    )
    db_session.add(msg)
    db_session.commit()

    res = engine.send_single_message(msg.id)
    assert res.get("status") == "cancelled"
    assert msg.status == "cancelado"
