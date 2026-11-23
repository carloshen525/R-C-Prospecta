from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.sending_daily_usage import SendingDailyUsage
from app.schemas.dashboard import DashboardResponse, DashboardIndicators, DayMetrics, SegmentDistribution, ActivityItem
from app.core.scheduler_rules import is_within_sending_window, get_now_in_brazil
from app.config import settings

router = APIRouter()

@router.get("", response_model=DashboardResponse)
def get_dashboard_data(db: Session = Depends(get_db)):
    # 1. Indicadores principais
    total_leads = db.query(Lead).count()
    leads_extracted = db.query(Lead).filter(Lead.source != "Manual").count()
    leads_available = db.query(Lead).filter(
        Lead.is_eligible == True,
        Lead.status.in_(["novo", "aguardando_processamento", "mensagens_geradas"])
    ).count()

    today_date = get_now_in_brazil().date()
    usage = db.query(SendingDailyUsage).filter(SendingDailyUsage.usage_date == today_date).first()
    contacts_sent_today = usage.contacts_sent_count if usage else 0
    daily_limit = usage.limit_max if usage else settings.DAILY_CONTACT_LIMIT
    remaining_today = max(0, daily_limit - contacts_sent_today)

    total_messages_sent = db.query(Message).filter(Message.status.in_(["enviado", "entregue", "lido"])).count()
    total_replies = db.query(Lead).filter(Lead.status.in_(["respondeu", "interessado", "sem_interesse"])).count()
    total_interested = db.query(Lead).filter(Lead.status == "interessado").count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "ativa").count()

    is_window_open, window_msg = is_within_sending_window()

    indicators = DashboardIndicators(
        total_leads=total_leads,
        leads_extracted=leads_extracted,
        leads_available=leads_available,
        contacts_sent_today=contacts_sent_today,
        daily_limit=daily_limit,
        remaining_today=remaining_today,
        total_messages_sent=total_messages_sent,
        total_replies=total_replies,
        total_interested=total_interested,
        active_campaigns=active_campaigns,
        is_window_open=is_window_open,
        window_status_message=window_msg
    )

    # 2. Gráfico dos últimos 7 dias (Envios vs Respostas)
    chart_daily_activity: list[DayMetrics] = []
    for i in range(6, -1, -1):
        d = today_date - timedelta(days=i)
        start_d = datetime.combine(d, datetime.min.time())
        end_d = datetime.combine(d, datetime.max.time())

        sent_count = db.query(Message).filter(
            Message.sent_at >= start_d,
            Message.sent_at <= end_d,
            Message.status.in_(["enviado", "entregue", "lido"])
        ).count()

        reply_count = db.query(Conversation).filter(
            Conversation.last_message_at >= start_d,
            Conversation.last_message_at <= end_d
        ).count()

        chart_daily_activity.append(DayMetrics(
            date=d.strftime("%d/%m"),
            sent=sent_count,
            replies=reply_count
        ))

    # 3. Distribuição por segmento
    segment_rows = db.query(Lead.segment, func.count(Lead.id)).filter(Lead.segment != None).group_by(Lead.segment).limit(5).all()
    chart_segments = [SegmentDistribution(segment=row[0] or "Geral", count=row[1]) for row in segment_rows]
    if not chart_segments and total_leads > 0:
        chart_segments.append(SegmentDistribution(segment="Outros", count=total_leads))

    # 4. Atividades recentes reais
    recent_activities: list[ActivityItem] = []
    
    # Últimas mensagens enviadas
    recent_messages = db.query(Message).join(Lead).filter(Message.status == "enviado").order_by(Message.sent_at.desc()).limit(3).all()
    for m in recent_messages:
        recent_activities.append(ActivityItem(
            id=f"msg_{m.id}",
            type="message_sent",
            title=f"Mensagem enviada (Parte {m.part_number})",
            description=f"Destinatário: {m.lead.company_name} ({m.lead.phone})",
            timestamp=m.sent_at.strftime("%H:%M - %d/%m") if m.sent_at else "Hoje"
        ))

    # Últimos leads cadastrados/extraídos
    recent_leads = db.query(Lead).order_by(Lead.created_at.desc()).limit(3).all()
    for l in recent_leads:
        recent_activities.append(ActivityItem(
            id=f"lead_{l.id}",
            type="extraction",
            title=f"Lead cadastrado: {l.company_name}",
            description=f"{l.segment or 'Segmento não informado'} - {l.city or 'Local não informado'}",
            timestamp=l.created_at.strftime("%H:%M - %d/%m")
        ))

    return DashboardResponse(
        indicators=indicators,
        chart_daily_activity=chart_daily_activity,
        chart_segments=chart_segments,
        recent_activities=recent_activities
    )
