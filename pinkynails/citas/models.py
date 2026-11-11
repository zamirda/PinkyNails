from urllib.parse import quote

from django.db import models
from django.db.models import Q
from django.utils import timezone

SERVICIOS = [
    ("Uñas de manos", "Uñas de manos"),
    ("Uñas de pies", "Uñas de pies"),
    ("Manos y pies", "Manos y pies"),
]


def etiqueta_hora(h):
    return f"{h if h <= 12 else h - 12}:00 {'a. m.' if h < 12 else 'p. m.'}"


class Cita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        CONFIRMADA = "confirmada", "Confirmada"
        CANCELADA = "cancelada", "Cancelada"

    servicio = models.CharField(max_length=30, choices=SERVICIOS)
    nombre = models.CharField(max_length=60)
    telefono = models.CharField(max_length=20, help_text="Con indicativo, solo números. Ej: 573001234567")
    inicio = models.DateTimeField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    creada = models.DateTimeField(auto_now_add=True)
    gcal_id = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["inicio"]
        constraints = [
            # Dos citas activas no pueden tener la misma hora (también protege de dos clientas a la vez).
            models.UniqueConstraint(
                fields=["inicio"],
                condition=~Q(estado="cancelada"),
                name="cita_unica_por_hora",
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.servicio} - {timezone.localtime(self.inicio):%Y-%m-%d %H:%M}"

    @property
    def hora_texto(self):
        return etiqueta_hora(timezone.localtime(self.inicio).hour)

    @property
    def wa_url(self):
        d = timezone.localtime(self.inicio)
        texto = (f"Hola {self.nombre}, te esperamos el {d:%d/%m/%Y} a las {self.hora_texto} "
                 f"en pinkynails.ym ({self.servicio}). ¿Confirmas tu asistencia?")
        return f"https://wa.me/{self.telefono}?text={quote(texto)}"


class Bloqueo(models.Model):
    """Día u hora en que no se atiende (vacaciones, citas personales...)."""
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True, help_text="Déjala vacía para bloquear todo el día.")
    motivo = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["fecha", "hora"]

    def __str__(self):
        return f"{self.fecha} {self.hora or 'todo el día'}"


class Foto(models.Model):
    """Fotos de la galería. Si no hay ninguna, se muestran las de ejemplo."""
    titulo = models.CharField(max_length=80, blank=True)
    imagen = models.ImageField(upload_to="trabajos/")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "id"]

    def __str__(self):
        return self.titulo or f"Foto {self.pk}"
