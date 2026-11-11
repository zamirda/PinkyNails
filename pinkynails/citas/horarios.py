from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Bloqueo, Cita, etiqueta_hora

HORAS = [7, 8, 9, 10, 11, 14, 15, 16, 17]  # inicio de cada cita; cada una dura 1 hora
DIAS_ADELANTE = 14
DIAS_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def etiqueta_dia(d):
    return f"{DIAS_ES[d.weekday()]} {d.day} {MESES_ES[d.month - 1]}"


def _ocupadas(desde, hasta):
    """Conjunto de (fecha, hora) que ya no están disponibles."""
    tz = timezone.get_current_timezone()
    ini = timezone.make_aware(datetime.combine(desde, time.min), tz)
    fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min), tz)
    ocupadas = set()
    for c in Cita.objects.exclude(estado=Cita.Estado.CANCELADA).filter(inicio__gte=ini, inicio__lt=fin):
        l = timezone.localtime(c.inicio)
        ocupadas.add((l.date(), l.hour))
    for b in Bloqueo.objects.filter(fecha__gte=desde, fecha__lte=hasta):
        if b.hora is None:
            ocupadas.update((b.fecha, h) for h in HORAS)
        else:
            ocupadas.add((b.fecha, b.hora.hour))
    return ocupadas


def libres():
    """Lista de (fecha, [horas libres]) solo con días que tengan al menos una hora libre."""
    ahora = timezone.localtime()
    hoy = ahora.date()
    fin = hoy + timedelta(days=DIAS_ADELANTE)
    ocupadas = _ocupadas(hoy, fin)
    resultado = []
    for i in range(DIAS_ADELANTE + 1):
        dia = hoy + timedelta(days=i)
        horas = [h for h in HORAS
                 if (dia, h) not in ocupadas and not (dia == hoy and h <= ahora.hour)]
        if horas:
            resultado.append((dia, horas))
    return resultado


def esta_libre(dia, hora):
    return any(d == dia and hora in horas for d, horas in libres())


def para_json():
    return {d.isoformat(): [{"v": h, "t": etiqueta_hora(h)} for h in horas] for d, horas in libres()}
