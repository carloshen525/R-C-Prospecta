from datetime import datetime
import pytz
from app.core.scheduler_rules import (
    is_within_sending_window,
    get_next_allowed_window_start,
    adjust_to_business_hours,
    BRAZIL_TZ
)

def test_window_open_at_10am():
    # 10:00 da manhã no fuso de SP deve estar aberto
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 20, 10, 0, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is True
    assert "aberta" in msg

def test_window_closed_at_19pm():
    # 19:00 da noite no fuso de SP deve estar fechado (pausa obrigatória)
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 20, 19, 0, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is False
    assert "Pausa obrigatória" in msg

def test_window_closed_at_06am():
    # 06:30 da manhã no fuso de SP deve estar fechado
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 20, 6, 30, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is False

def test_window_exact_boundary_1830():
    # 18:30 no limite deve estar aberto (20/11/2026 é sexta-feira)
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 20, 18, 30, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is True

def test_window_closed_on_saturday():
    # Sábado (21/11/2026) às 10:00 deve estar rigorosamente fechado
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 21, 10, 0, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is False
    assert "Sábado" in msg

def test_window_closed_on_sunday():
    # Domingo (22/11/2026) às 14:00 deve estar rigorosamente fechado
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 22, 14, 0, 0))
    is_open, msg = is_within_sending_window(dt)
    assert is_open is False
    assert "Domingo" in msg

def test_next_allowed_window_calculation_skips_weekend():
    # Se for sexta-feira 20:00 (20/11/2026), pula sábado (21) e domingo (22), caindo na segunda-feira (23/11/2026) às 07:00
    dt = BRAZIL_TZ.localize(datetime(2026, 11, 20, 20, 0, 0))
    next_start = get_next_allowed_window_start(dt)
    assert next_start.day == 23  # Segunda-feira
    assert next_start.hour == 7
    assert next_start.minute == 0
