from datetime import date, timedelta

TAG_BASE = "Agenda tu cita en un minuto y llega lista para brillar."

TEMAS = {
    "mujer": {"tag": "Este mes celebramos a las mujeres que brillan. 💜", "evento": "💜 Feliz Día de la Mujer", "fx": ["💜", "🌷"]},
    "madre": {"tag": "Regálale a mamá unas uñas hermosas. 🌷", "evento": "🌷 Feliz Día de la Madre", "fx": ["🌸", "🌷"]},
    "semana": {"tag": "Tiempo de calma y recogimiento. Agenda tu cita con tiempo.", "evento": "Semana Santa", "fx": []},
    "octubre": {"tag": "Uñas de miedo... ¡pero de lo bonitas! Agenda tu cita.", "evento": "🎃 Noches de Halloween", "fx": ["🎃", "🦇"]},
    "dic": {"tag": "Estrena uñas para las fiestas. ¡Agenda ya!", "evento": "🎄 Feliz Navidad", "fx": ["❄️", "✨"]},
}


def pascua(y):
    a = y % 19
    b, c = divmod(y, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(y, mes, dia)


def actual(hoy):
    """Devuelve la clave del tema según la fecha ('base' si no hay evento)."""
    p = pascua(hoy.year)
    if p - timedelta(days=7) <= hoy <= p:
        return "semana"
    if hoy.month == 3 and hoy.day <= 10:
        return "mujer"
    if hoy.month == 5:
        primer = date(hoy.year, 5, 1)
        primer_domingo = 1 + (6 - primer.weekday()) % 7
        if hoy.day <= primer_domingo + 7:  # hasta el segundo domingo de mayo
            return "madre"
    if hoy.month == 10:
        return "octubre"
    if hoy.month == 12:
        return "dic"
    return "base"
