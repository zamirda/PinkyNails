import logging
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings
from django.utils import timezone

log = logging.getLogger(__name__)


def whatsapp(telefono, clave, texto):
    """Manda un WhatsApp con CallMeBot. Devuelve True si el servicio respondió bien."""
    if not (telefono and clave):
        return False
    url = "https://api.callmebot.com/whatsapp.php?" + urlencode({"phone": telefono, "text": texto, "apikey": clave})
    try:
        with urlopen(url, timeout=10) as r:
            return 200 <= r.status < 300
    except Exception:
        log.exception("No se pudo enviar el WhatsApp")
        return False


def _calendar():
    if not (settings.GOOGLE_CALENDAR_ID and settings.GOOGLE_CREDENTIALS_FILE):
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def crear_evento(cita):
    try:
        svc = _calendar()
        if svc is None:
            return
        fin = cita.inicio + timedelta(hours=1)
        cuerpo = {
            "summary": f"💅 {cita.servicio} - {cita.nombre}",
            "description": f"Clienta: {cita.nombre}\nWhatsApp: {cita.telefono}\nServicio: {cita.servicio}",
            "start": {"dateTime": cita.inicio.isoformat(), "timeZone": settings.TIME_ZONE},
            "end": {"dateTime": fin.isoformat(), "timeZone": settings.TIME_ZONE},
            "reminders": {"useDefault": False, "overrides": [
                {"method": "popup", "minutes": 60}, {"method": "popup", "minutes": 1440}]},
        }
        ev = svc.events().insert(calendarId=settings.GOOGLE_CALENDAR_ID, body=cuerpo).execute()
        cita.gcal_id = ev["id"]
        cita.save(update_fields=["gcal_id"])
    except Exception:
        log.exception("No se pudo crear el evento en Google Calendar")


def borrar_evento(cita):
    if not cita.gcal_id:
        return
    try:
        svc = _calendar()
        if svc is not None:
            svc.events().delete(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=cita.gcal_id).execute()
    except Exception:
        log.exception("No se pudo borrar el evento de Google Calendar")


def avisar_cita(cita):
    """Se llama al agendar. Si algo falla, la cita igual queda guardada."""
    d = timezone.localtime(cita.inicio)
    texto = (f"Nueva cita en {settings.NEGOCIO}: {cita.servicio}, {cita.nombre}, "
             f"{d:%d/%m/%Y} a las {cita.hora_texto}. WhatsApp de la clienta: +{cita.telefono}")
    whatsapp(settings.WA_PHONE, settings.WA_KEY, texto)
    crear_evento(cita)
