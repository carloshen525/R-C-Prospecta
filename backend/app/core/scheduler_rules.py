from datetime import datetime, time, timedelta
from typing import Optional, Tuple, Any
import pytz
from app.config import settings

BRAZIL_TZ = pytz.timezone(settings.TIMEZONE)

def get_now_in_brazil() -> datetime:
    """Retorna o datetime atual no fuso horário America/Sao_Paulo"""
    return datetime.now(BRAZIL_TZ)

def is_within_sending_window(dt: Optional[datetime] = None, db: Optional[Any] = None) -> Tuple[bool, str]:
    """
    Verifica se o horário e dia da semana estão dentro da janela permitida:
    Por padrão: 07:00 às 18:30 (America/Sao_Paulo), de segunda a sexta.
    Lê dinamicamente as preferências salvas no banco caso disponíveis.
    """
    if dt is None:
        dt = get_now_in_brazil()
    elif dt.tzinfo is None:
        dt = BRAZIL_TZ.localize(dt)
    else:
        dt = dt.astimezone(BRAZIL_TZ)

    start_h = settings.SENDING_START_HOUR
    start_m = settings.SENDING_START_MINUTE
    end_h = settings.SENDING_END_HOUR
    end_m = settings.SENDING_END_MINUTE
    allowed_days_list = ["seg", "ter", "qua", "qui", "sex"]

    # Se db não foi passado, tenta abrir uma sessão rápida
    target_db = db
    should_close = False
    if target_db is None:
        try:
            from app.database import SessionLocal
            target_db = SessionLocal()
            should_close = True
        except Exception:
            pass

    if target_db:
        try:
            from app.models.setting import Setting
            for s in target_db.query(Setting).all():
                if s.key == "SENDING_START_HOUR" and s.value:
                    start_h = int(s.value)
                elif s.key == "SENDING_START_MINUTE" and s.value:
                    start_m = int(s.value)
                elif s.key == "SENDING_END_HOUR" and s.value:
                    end_h = int(s.value)
                elif s.key == "SENDING_END_MINUTE" and s.value:
                    end_m = int(s.value)
                elif s.key == "AUTOMATION_ALLOWED_DAYS" and s.value:
                    allowed_days_list = [d.strip().lower() for d in s.value.split(",") if d.strip()]
        except Exception:
            pass
        finally:
            if should_close:
                target_db.close()

    # Validação do dia da semana (0=seg, 1=ter, 2=qua, 3=qui, 4=sex, 5=sab, 6=dom)
    weekday_map = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex", 5: "sab", 6: "dom"}
    weekday_names = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    current_day_code = weekday_map.get(dt.weekday(), "seg")

    # Validação rigorosa: Sábado (5) e Domingo (6) nunca realizam disparos
    if dt.weekday() in (5, 6):
        day_name = "Sábado" if dt.weekday() == 5 else "Domingo"
        return False, f"Pausa obrigatória de fim de semana: {day_name}s não possuem disparos de prospecção."

    # Validação dos dias permitidos configurados pelo usuário
    if allowed_days_list and current_day_code not in allowed_days_list:
        return False, f"Dia não permitido para envios ({weekday_names.get(dt.weekday(), current_day_code)}). Envio pausado até o próximo dia útil."

    current_time = dt.time()
    start_time = time(start_h, start_m)
    end_time = time(end_h, end_m)

    if start_time <= current_time <= end_time:
        return True, "Janela de envio aberta"
    else:
        return False, f"Pausa obrigatória ativa fora do horário configurado ({end_time.strftime('%H:%M')} às {start_time.strftime('%H:%M')})"

def get_next_allowed_window_start(dt: Optional[datetime] = None) -> datetime:
    """
    Calcula o próximo momento válido de envio (07:00 no fuso de SP).
    Se for após 18:30, o próximo início será amanhã às 07:00.
    Se for antes das 07:00, será hoje às 07:00.
    Pula rigorosamente sábado e domingo, avançando para segunda-feira às 07:00.
    """
    if dt is None:
        dt = get_now_in_brazil()
    elif dt.tzinfo is None:
        dt = BRAZIL_TZ.localize(dt)
    else:
        dt = dt.astimezone(BRAZIL_TZ)

    start_time = time(settings.SENDING_START_HOUR, settings.SENDING_START_MINUTE)
    end_time = time(settings.SENDING_END_HOUR, settings.SENDING_END_MINUTE)

    if dt.time() > end_time:
        next_day = dt.date() + timedelta(days=1)
        next_start = BRAZIL_TZ.localize(datetime.combine(next_day, start_time))
    elif dt.time() < start_time:
        next_start = BRAZIL_TZ.localize(datetime.combine(dt.date(), start_time))
    else:
        next_start = dt

    # Pula sábado (5) e domingo (6), avançando até a próxima segunda-feira
    while next_start.weekday() in (5, 6):
        next_day = next_start.date() + timedelta(days=1)
        next_start = BRAZIL_TZ.localize(datetime.combine(next_day, start_time))

    return next_start

def adjust_to_business_hours(target_dt: datetime) -> datetime:
    """
    Se o horário cair fora da janela (ex: 20:00 da noite),
    ajusta para o início da próxima janela útil (07:00 do dia seguinte).
    """
    if target_dt.tzinfo is None:
        target_dt = BRAZIL_TZ.localize(target_dt)
    else:
        target_dt = target_dt.astimezone(BRAZIL_TZ)

    is_open, _ = is_within_sending_window(target_dt)
    if not is_open:
        return get_next_allowed_window_start(target_dt)
    return target_dt
