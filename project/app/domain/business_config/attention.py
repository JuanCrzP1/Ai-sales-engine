"""Atención humana: cuándo hay alguien del equipo, qué se le dice al cliente y cuándo la IA retoma un chat que nadie atendió.

Son ajustes de la operación del negocio (Configuración → Atención humana): se aplican al instante, sin publicar una versión del asistente.
Lo que el asistente le dice al cliente en esos momentos sí es del asistente (Asistente IA → Mensajes) y se publica.

- **Horario del equipo:** el mismo de «Mi negocio», otro propio, o siempre hay alguien. Sin horario, siempre hay alguien.
- **Dentro del horario**, cuando un chat pasa a una persona, la IA se pausa y el cliente sabe cuánto suele tardar el equipo.
- **Fuera del horario**, el chat también queda esperando a una persona (el equipo lo ve al llegar), pero la IA no se pausa: le dice al
  cliente cuándo lo atienden y sigue ayudándole en lo que pueda.
- **La IA retoma sola** si el cliente lleva esperando más de lo que el negocio eligió y nadie del equipo respondió.

Todo aquí es puro: sin base de datos, sin red y sin reloj (la hora llega como argumento).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.domain.business_config.errors import FieldIssue, InvalidFieldsError

WEEKDAYS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
_WEEKDAY_NAMES = {"lunes": "lunes", "martes": "martes", "miercoles": "miércoles", "jueves": "jueves", "viernes": "viernes", "sabado": "sábado", "domingo": "domingo"}

# De dónde sale el horario del equipo.
HOURS_MODES = ("business", "custom", "always")
# Zonas horarias que se pueden elegir, con su nombre para el panel.
TIMEZONES: dict[str, str] = {
    "America/Bogota": "Colombia",
    "America/Mexico_City": "México (Ciudad de México)",
    "America/Lima": "Perú",
    "America/Guayaquil": "Ecuador",
    "America/Panama": "Panamá",
    "America/Caracas": "Venezuela",
    "America/Santiago": "Chile",
    "America/Argentina/Buenos_Aires": "Argentina",
    "America/Montevideo": "Uruguay",
    "America/Asuncion": "Paraguay",
    "America/La_Paz": "Bolivia",
    "America/Costa_Rica": "Costa Rica",
    "America/Guatemala": "Guatemala",
    "America/El_Salvador": "El Salvador",
    "America/Tegucigalpa": "Honduras",
    "America/Managua": "Nicaragua",
    "America/Santo_Domingo": "República Dominicana",
    "America/Puerto_Rico": "Puerto Rico",
    "America/New_York": "Estados Unidos (Este)",
    "America/Chicago": "Estados Unidos (Centro)",
    "America/Los_Angeles": "Estados Unidos (Pacífico)",
    "Europe/Madrid": "España",
}
DEFAULT_TIMEZONE = "America/Bogota"
# Lo que se le dice al cliente sobre cuánto tarda el equipo (0: no se le dice).
REPLY_MINUTES = (0, 5, 10, 15, 30, 60, 120, 240)
# Cuánto espera el cliente antes de que la IA retome el chat (None: nunca).
RESUME_MINUTES = (10, 15, 30, 45, 60, 120, 240)
DEFAULT_REPLY_MINUTES = 10
DEFAULT_RESUME_MINUTES = 30
MAX_HOURS_RANGES = 14
MAX_EMAIL_CHARS = 254
_CLOCK = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class HoursRange:
    """Unos días con su hora de entrada y de salida (HH:MM, 24 h), como el horario de «Mi negocio»."""

    days: tuple[str, ...]
    opens: str
    closes: str


@dataclass(frozen=True)
class AttentionSettings:
    hours_mode: str = "business"
    team_hours: tuple[HoursRange, ...] = ()
    timezone: str = DEFAULT_TIMEZONE
    reply_minutes: int = DEFAULT_REPLY_MINUTES
    resume_after_minutes: int | None = DEFAULT_RESUME_MINUTES
    email_enabled: bool = True
    # A quién le llega el correo. Sin él, a los dueños del negocio (el correo de su cuenta).
    email_to: str | None = None
    updated_at: datetime | None = field(default=None, compare=False)


@dataclass(frozen=True)
class HandoffPlan:
    """Qué pasa cuando un chat pasa a una persona: si la IA se pausa y qué se le dice al cliente (o nada)."""

    team_available: bool
    pause_ai: bool
    notice: str | None


# ---------------------------------------------------------------------------------------------------------- validar


def hours_from(raw: object) -> tuple[HoursRange, ...]:
    """Lee un horario guardado o publicado (lista de `{days, opens, closes}`). Lo que no se entiende se ignora."""
    ranges: list[HoursRange] = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        days = tuple(day for day in item.get("days") or [] if day in WEEKDAYS)
        opens, closes = str(item.get("opens") or ""), str(item.get("closes") or "")
        if days and _CLOCK.match(opens) and _CLOCK.match(closes) and opens < closes:
            ranges.append(HoursRange(days, opens, closes))
    return tuple(ranges)


def hours_payload(hours: tuple[HoursRange, ...]) -> list[dict]:
    return [{"days": list(item.days), "opens": item.opens, "closes": item.closes} for item in hours]


def validated(
    *,
    hours_mode: object,
    team_hours: object,
    timezone_name: object,
    reply_minutes: object,
    resume_after_minutes: object,
    email_enabled: object,
    email_to: object,
) -> AttentionSettings:
    """Los ajustes que llegan del panel, revisados campo por campo. Si algo no sirve, dice qué y dónde."""
    issues: list[FieldIssue] = []
    mode = str(hours_mode or "")
    if mode not in HOURS_MODES:
        issues.append(FieldIssue("hours_mode", "Elige de dónde sale el horario del equipo."))
    hours: list[HoursRange] = []
    raw_hours = team_hours if isinstance(team_hours, list) else []
    if not isinstance(team_hours, list) and team_hours is not None:
        issues.append(FieldIssue("team_hours", "El horario no tiene el formato esperado."))
    if len(raw_hours) > MAX_HOURS_RANGES:
        issues.append(FieldIssue("team_hours", f"Máximo {MAX_HOURS_RANGES} franjas."))
    for index, item in enumerate(raw_hours[:MAX_HOURS_RANGES]):
        path = f"team_hours[{index}]"
        if not isinstance(item, dict):
            issues.append(FieldIssue(path, "Esta franja no tiene el formato esperado."))
            continue
        days = item.get("days") if isinstance(item.get("days"), list) else []
        if not days or any(day not in WEEKDAYS for day in days) or len(set(days)) != len(days):
            issues.append(FieldIssue(f"{path}.days", "Elige al menos un día, sin repetir."))
        opens, closes = str(item.get("opens") or ""), str(item.get("closes") or "")
        if not _CLOCK.match(opens):
            issues.append(FieldIssue(f"{path}.opens", "Escribe la hora de entrada (HH:MM)."))
        if not _CLOCK.match(closes):
            issues.append(FieldIssue(f"{path}.closes", "Escribe la hora de salida (HH:MM)."))
        if _CLOCK.match(opens) and _CLOCK.match(closes) and opens >= closes:
            issues.append(FieldIssue(f"{path}.closes", "La hora de salida debe ser después de la de entrada."))
        hours.append(HoursRange(tuple(str(day) for day in days), opens, closes))
    if mode == "custom" and not raw_hours:
        issues.append(FieldIssue("team_hours", "Agrega al menos una franja, o elige otro horario."))
    zone = str(timezone_name or "")
    if zone not in TIMEZONES:
        issues.append(FieldIssue("timezone", "Elige la zona horaria del negocio."))
    if isinstance(reply_minutes, bool) or reply_minutes not in REPLY_MINUTES:
        issues.append(FieldIssue("reply_minutes", "Elige una de las opciones."))
    if resume_after_minutes is not None and (isinstance(resume_after_minutes, bool) or resume_after_minutes not in RESUME_MINUTES):
        issues.append(FieldIssue("resume_after_minutes", "Elige una de las opciones."))
    if not isinstance(email_enabled, bool):
        issues.append(FieldIssue("email_enabled", "Indica si quieres avisos por correo."))
    email = str(email_to or "").strip() or None
    if email is not None and (len(email) > MAX_EMAIL_CHARS or not _EMAIL.match(email)):
        issues.append(FieldIssue("email_to", "Escribe un correo válido, o déjalo vacío para usar el de tu cuenta."))
    if issues:
        raise InvalidFieldsError("Revisa la atención humana.", issues)
    return AttentionSettings(
        hours_mode=mode,
        team_hours=tuple(hours) if mode == "custom" else (),
        timezone=zone,
        reply_minutes=int(reply_minutes),  # type: ignore[arg-type]
        resume_after_minutes=int(resume_after_minutes) if resume_after_minutes is not None else None,  # type: ignore[arg-type]
        email_enabled=bool(email_enabled),
        email_to=email,
    )


# ---------------------------------------------------------------------------------------------------------- horario


def team_hours(settings: AttentionSettings, business_hours: tuple[HoursRange, ...]) -> tuple[HoursRange, ...]:
    """El horario en que hay alguien del equipo. Vacío: siempre hay alguien."""
    if settings.hours_mode == "always":
        return ()
    if settings.hours_mode == "custom":
        return settings.team_hours
    return business_hours


def _zone(settings: AttentionSettings) -> ZoneInfo:
    return ZoneInfo(settings.timezone if settings.timezone in TIMEZONES else DEFAULT_TIMEZONE)


def _clock(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def _ranges_on(hours: tuple[HoursRange, ...], day: date) -> list[tuple[time, time]]:
    weekday = WEEKDAYS[day.weekday()]
    return sorted((_clock(item.opens), _clock(item.closes)) for item in hours if weekday in item.days)


def is_open(hours: tuple[HoursRange, ...], zone: ZoneInfo, now: datetime) -> bool:
    if not hours:
        return True
    local = now.astimezone(zone)
    return any(opens <= local.time() < closes for opens, closes in _ranges_on(hours, local.date()))


def next_opening(hours: tuple[HoursRange, ...], zone: ZoneInfo, now: datetime) -> datetime | None:
    """La próxima vez que entra alguien del equipo (en UTC), o None si no hay horario."""
    if not hours:
        return None
    local = now.astimezone(zone)
    for offset in range(8):
        day = local.date() + timedelta(days=offset)
        for opens, _closes in _ranges_on(hours, day):
            candidate = datetime.combine(day, opens, tzinfo=zone)
            if candidate > local:
                return candidate.astimezone(timezone.utc)
    return None


# ---------------------------------------------------------------------------------------------------------- textos


def clock_text(value: time) -> str:
    """«8:00 a. m.», «1:30 p. m.», «12:00 m.»."""
    if value.hour == 12 and value.minute == 0:
        return "12:00 m."
    hour = value.hour % 12 or 12
    return f"{hour}:{value.minute:02d} {'a. m.' if value.hour < 12 else 'p. m.'}"


def _at(value: time) -> str:
    return f"a la {clock_text(value)}" if value.hour % 12 == 1 else f"a las {clock_text(value)}"


def when_text(moment: datetime, zone: ZoneInfo, now: datetime) -> str:
    """Cuándo, dicho como lo diría una persona: «hoy a las 3:00 p. m.», «mañana a las 8:00 a. m.», «el lunes a las 8:00 a. m.»."""
    local, today = moment.astimezone(zone), now.astimezone(zone).date()
    days = (local.date() - today).days
    if days <= 0:
        prefix = "hoy"
    elif days == 1:
        prefix = "mañana"
    else:
        prefix = f"el {_WEEKDAY_NAMES[WEEKDAYS[local.weekday()]]}"
    return f"{prefix} {_at(local.time())}"


def _days_text(days: tuple[str, ...]) -> str:
    ordered = sorted(set(days), key=WEEKDAYS.index)
    if len(ordered) == 7:
        return "todos los días"
    indexes = [WEEKDAYS.index(day) for day in ordered]
    names = [_WEEKDAY_NAMES[day] for day in ordered]
    if len(ordered) == 1:
        return f"el {names[0]}" if ordered[0] != "domingo" else "el domingo"
    if len(ordered) >= 3 and indexes == list(range(indexes[0], indexes[-1] + 1)):
        return f"de {names[0]} a {names[-1]}"
    return f"{', '.join(names[:-1])} y {names[-1]}"


def hours_text(hours: tuple[HoursRange, ...]) -> str:
    """El horario dicho en una frase: «de lunes a viernes de 8:00 a. m. a 6:00 p. m. y el sábado de 9:00 a. m. a 1:00 p. m.»."""
    parts = [f"{_days_text(item.days)} de {clock_text(_clock(item.opens))} a {clock_text(_clock(item.closes))}" for item in hours]
    return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} y {parts[-1]}"


def wait_text(minutes: int) -> str:
    """«unos 10 minutos», «una hora», «unas 2 horas»."""
    if minutes < 60:
        return f"unos {minutes} minutos"
    if minutes == 60:
        return "una hora"
    return f"unas {minutes // 60} horas" if minutes % 60 == 0 else f"unos {minutes} minutos"


def _sentence(text: str) -> str:
    # Las horas terminan en «a. m.»: no se les agrega otro punto.
    return text if text.endswith(".") else f"{text}."


def default_after_hours_notice(hours: tuple[HoursRange, ...], back: datetime | None, zone: ZoneInfo, now: datetime) -> str:
    parts = [_sentence(f"Nuestro equipo atiende {hours_text(hours)}")]
    if back is not None:
        parts.append(_sentence(f"Una persona te escribirá {when_text(back, zone, now)}"))
    parts.append("Mientras tanto, sigo aquí para ayudarte en lo que pueda.")
    return " ".join(parts)


DEFAULT_RESUMED_NOTICE = "Disculpa la espera. Mientras alguien del equipo se libera, sigo ayudándote yo."


def handoff_plan(
    settings: AttentionSettings,
    business_hours: tuple[HoursRange, ...],
    now: datetime,
    *,
    after_hours_message: str | None = None,
) -> HandoffPlan:
    """Qué pasa al pasar un chat a una persona. Dentro del horario, la IA se pausa y el cliente sabe cuánto suele tardar el equipo;
    fuera de él, la IA sigue y le dice cuándo lo atienden (con el mensaje del negocio, si lo escribió)."""
    hours, zone = team_hours(settings, business_hours), _zone(settings)
    if is_open(hours, zone, now):
        notice = f"Una persona de nuestro equipo te responderá en {wait_text(settings.reply_minutes)}." if settings.reply_minutes else None
        return HandoffPlan(team_available=True, pause_ai=True, notice=notice)
    custom = str(after_hours_message or "").strip()
    notice = custom or default_after_hours_notice(hours, next_opening(hours, zone, now), zone, now)
    return HandoffPlan(team_available=False, pause_ai=False, notice=notice)


def resume_due(settings: AttentionSettings, waiting_since: datetime | None, now: datetime) -> bool:
    """Si la IA debe retomar un chat pausado: el cliente lleva esperando más de lo elegido y nadie del equipo respondió."""
    if waiting_since is None or settings.resume_after_minutes is None:
        return False
    return now - waiting_since >= timedelta(minutes=settings.resume_after_minutes)


def with_updated_at(settings: AttentionSettings, updated_at: datetime | None) -> AttentionSettings:
    return replace(settings, updated_at=updated_at)


@dataclass(frozen=True)
class PublishedAttention:
    """Lo publicado del negocio que usa la atención humana: su horario (el de «Mi negocio») y sus dos mensajes, si los escribió."""

    business_hours: tuple[HoursRange, ...] = ()
    after_hours: str | None = None
    ai_resumed: str | None = None


def published_attention(sections: dict) -> PublishedAttention:
    """Lee lo compilado de la versión publicada (`compile_business_config`): `config.profile.opening_hours` y
    `config.attention_messages`. Sin ellos, valores vacíos: la plataforma usa sus mensajes."""
    config = sections.get("config") if isinstance(sections, dict) and isinstance(sections.get("config"), dict) else {}
    profile = config.get("profile") if isinstance(config.get("profile"), dict) else {}
    messages = config.get("attention_messages") if isinstance(config.get("attention_messages"), dict) else {}
    return PublishedAttention(
        business_hours=hours_from(profile.get("opening_hours")),
        after_hours=str(messages.get("after_hours") or "").strip() or None,
        ai_resumed=str(messages.get("ai_resumed") or "").strip() or None,
    )
