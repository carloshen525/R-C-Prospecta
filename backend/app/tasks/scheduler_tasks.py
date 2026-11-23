from app.celery_app import celery
from app.database import SessionLocal
from app.core.scheduler_rules import is_within_sending_window, get_now_in_brazil
from app.models.sending_daily_usage import SendingDailyUsage
from app.core.logging import logger

@celery.task(name="app.tasks.scheduler_tasks.monitor_daily_cycle")
def monitor_daily_cycle():
    """
    Monitora a janela de envio útil (07:00 às 18:30 no fuso de São Paulo).
    Garante o reset diário de contatos à meia-noite e loga o estado da janela.
    """
    now = get_now_in_brazil()
    is_open, status_msg = is_within_sending_window(now)

    db = SessionLocal()
    try:
        today_date = now.date()
        usage = db.query(SendingDailyUsage).filter(SendingDailyUsage.usage_date == today_date).first()
        usage_str = f"{usage.contacts_sent_count}/{usage.limit_max}" if usage else "0/30"

        logger.info(
            f"[Cycle Monitor] Hora em SP: {now.strftime('%d/%m/%Y %H:%M:%S')} | "
            f"Janela: {'ABERTA' if is_open else 'FECHADA'} ({status_msg}) | "
            f"Consumo diário: {usage_str}"
        )
        return {
            "current_time_sp": str(now),
            "is_window_open": is_open,
            "status_message": status_msg,
            "daily_usage": usage_str
        }
    finally:
        db.close()
