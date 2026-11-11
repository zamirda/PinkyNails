import re
import secrets
import time
from datetime import date, datetime, timedelta, time as hora_t
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import horarios, services, temporadas
from .models import SERVICIOS, Cita, Foto, etiqueta_hora

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="citas:login")


def _ip(request):
    return request.META.get("REMOTE_ADDR", "x")


def _digitos(tel):
    return re.sub(r"\D", "", tel or "")


def index(request):
    tema = temporadas.actual(timezone.localdate())
    pedido = request.GET.get("tema")
    if pedido and request.user.is_staff and (pedido == "base" or pedido in temporadas.TEMAS):
        tema = pedido  # vista previa solo para la administradora
    datos = temporadas.TEMAS.get(tema)
    fotos = list(Foto.objects.all())
    if fotos:
        galeria = [{"url": f.imagen.url, "alt": f.titulo or "Trabajo de uñas"} for f in fotos]
    else:
        galeria = [{"url": static(f"citas/demo/trabajo-{i}.jpg"), "alt": f"Diseño de uñas de ejemplo {i}"}
                   for i in range(1, 9)]
    libres = horarios.libres()
    slots = {d.isoformat(): [{"v": h, "t": etiqueta_hora(h)} for h in hs] for d, hs in libres}
    dias = {d.isoformat(): horarios.etiqueta_dia(d) for d, _ in libres}
    return render(request, "citas/index.html", {
        "tema": tema,
        "tag": datos["tag"] if datos else temporadas.TAG_BASE,
        "evento": datos["evento"] if datos else "",
        "fx": datos["fx"] if datos else [],
        "galeria": galeria,
        "servicios": [s[0] for s in SERVICIOS],
        "slots": slots,
        "dias": dias,
    })


@require_POST
def agendar(request):
    ip = _ip(request)
    clave = f"agendar:{ip}"
    n = cache.get(clave, 0)
    if n >= 10:
        return JsonResponse({"ok": False, "error": "Demasiados intentos. Prueba más tarde."}, status=429)
    cache.set(clave, n + 1, 3600)

    servicio = request.POST.get("servicio", "")
    nombre = request.POST.get("nombre", "").strip()[:60]
    tel = _digitos(request.POST.get("telefono"))
    if len(tel) == 10 and tel.startswith("3"):
        tel = "57" + tel  # celular colombiano sin indicativo
    try:
        dia = date.fromisoformat(request.POST.get("fecha", ""))
        hora = int(request.POST.get("hora", ""))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Escoge un día y una hora."}, status=400)
    if servicio not in dict(SERVICIOS) or len(nombre) < 2 or not 10 <= len(tel) <= 13:
        return JsonResponse({"ok": False, "error": "Revisa tu nombre, tu WhatsApp y el servicio."}, status=400)
    if not horarios.esta_libre(dia, hora):
        return JsonResponse({"ok": False, "error": "Esa hora ya no está disponible. Escoge otra."}, status=409)

    inicio = timezone.make_aware(datetime.combine(dia, hora_t(hora)))
    try:
        with transaction.atomic():
            cita = Cita.objects.create(servicio=servicio, nombre=nombre, telefono=tel, inicio=inicio)
    except IntegrityError:
        return JsonResponse({"ok": False, "error": "Esa hora acaba de ocuparse. Escoge otra."}, status=409)

    services.avisar_cita(cita)
    texto = (f"Hola, soy {nombre}. Agendé {servicio} para el {dia:%d/%m/%Y} a las {cita.hora_texto}. "
             "Confirmo mi asistencia.")
    wa = f"https://wa.me/{_digitos(settings.WA_PHONE)}?text={quote(texto)}"
    return JsonResponse({"ok": True, "mensaje": f"Cita agendada para el {dia:%d/%m/%Y} a las {cita.hora_texto}.", "wa_url": wa})


# ---------------- Panel de la administradora ----------------

def entrar(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("citas:panel")
    if request.method == "POST":
        clave = f"login:{_ip(request)}"
        fallos = cache.get(clave, 0)
        if fallos >= 5:
            messages.error(request, "Demasiados intentos. Espera 10 minutos.")
        else:
            user = authenticate(request, username=request.POST.get("usuario", "").strip(),
                                password=request.POST.get("password", ""))
            if user is not None and user.is_staff:
                login(request, user)
                cache.delete(clave)
                return redirect("citas:panel")
            cache.set(clave, fallos + 1, 600)
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, "citas/login.html", {"tema": "base"})


@require_POST
def salir(request):
    logout(request)
    return redirect("citas:index")


@staff_required
def panel(request):
    if request.method == "POST":
        cita = get_object_or_404(Cita, pk=request.POST.get("id"))
        accion = request.POST.get("accion")
        if accion == "confirmar":
            cita.estado = Cita.Estado.CONFIRMADA
            cita.save(update_fields=["estado"])
        elif accion == "cancelar":
            cita.estado = Cita.Estado.CANCELADA
            cita.save(update_fields=["estado"])
            services.borrar_evento(cita)
        return redirect("citas:panel")
    desde = timezone.now() - timedelta(hours=2)
    citas = Cita.objects.exclude(estado=Cita.Estado.CANCELADA).filter(inicio__gte=desde)
    return render(request, "citas/panel.html", {"tema": "base", "citas": citas})


@staff_required
def cuenta(request):
    pend = request.session.get("cambio")
    if pend and pend["exp"] < time.time():
        request.session.pop("cambio", None)
        pend = None
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "pedir":
            usuario = request.POST.get("usuario", "").strip()
            pw = request.POST.get("password", "")
            if not re.fullmatch(r"[\w.@+-]{4,30}", usuario):
                messages.error(request, "El usuario debe tener entre 4 y 30 caracteres (letras, números o . @ + - _).")
            elif len(pw) < 8:
                messages.error(request, "La contraseña debe tener 8 caracteres o más.")
            elif User.objects.exclude(pk=request.user.pk).filter(username=usuario).exists():
                messages.error(request, "Ese usuario ya existe.")
            else:
                codigo = f"{secrets.randbelow(900000) + 100000}"
                enviado = services.whatsapp(
                    settings.VERIFY_PHONE, settings.VERIFY_KEY,
                    f"{settings.NEGOCIO}: tu código de verificación es {codigo}. Vence en 10 minutos.")
                if enviado or settings.DEBUG:
                    request.session["cambio"] = {"u": usuario, "p": make_password(pw), "c": make_password(codigo),
                                                 "exp": time.time() + 600, "n": 0}
                    if enviado:
                        messages.success(request, "Te enviamos un código por WhatsApp al celular registrado.")
                    else:  # solo en pruebas locales (DEBUG)
                        messages.info(request, f"Modo pruebas: WhatsApp no está configurado. El código es {codigo}.")
                else:
                    messages.error(request, "No se pudo enviar el código. Intenta de nuevo en un momento.")
        elif accion == "confirmar" and pend:
            if pend["n"] >= 5:
                request.session.pop("cambio", None)
                messages.error(request, "Demasiados intentos. Pide un código nuevo.")
            elif check_password(request.POST.get("codigo", "").strip(), pend["c"]):
                user = request.user
                user.username = pend["u"]
                user.password = pend["p"]  # ya viene cifrada
                user.save()
                update_session_auth_hash(request, user)
                request.session.pop("cambio", None)
                messages.success(request, "Listo. Usa el nuevo usuario y contraseña la próxima vez.")
            else:
                pend["n"] += 1
                request.session["cambio"] = pend
                messages.error(request, "Código incorrecto.")
        return redirect("citas:cuenta")
    return render(request, "citas/cuenta.html", {"tema": "base", "pendiente": bool(pend)})
