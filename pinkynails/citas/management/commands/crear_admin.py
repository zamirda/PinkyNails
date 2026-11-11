from getpass import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea (o actualiza) el usuario administrador del panel."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="yilemor")
        parser.add_argument("--password", default=None, help="Si no la pasas, te la pide sin mostrarla.")

    def handle(self, *args, **o):
        pw = o["password"] or getpass("Contraseña: ")
        if len(pw) < 8:
            raise CommandError("La contraseña debe tener 8 caracteres o más.")
        u, creado = User.objects.get_or_create(username=o["usuario"])
        u.is_staff = u.is_superuser = True
        u.set_password(pw)
        u.save()
        self.stdout.write(self.style.SUCCESS(f"Usuario {u.username} {'creado' if creado else 'actualizado'}."))
