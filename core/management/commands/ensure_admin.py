"""Crea o actualiza un superusuario a partir de variables de entorno.

Pensado para correr en cada deploy (ver buildCommand en render.yaml), ya que
en el plan free de Render la base se puede recrear. Si DJANGO_ADMIN_USERNAME
o DJANGO_ADMIN_PASSWORD no están seteadas, no hace nada — así que en
desarrollo local (donde no existen esas variables) este comando es un no-op
seguro.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crea o actualiza el superusuario de DJANGO_ADMIN_USERNAME con la "
        "contraseña de DJANGO_ADMIN_PASSWORD. No hace nada si esas "
        "variables de entorno no están definidas."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "DJANGO_ADMIN_USERNAME/DJANGO_ADMIN_PASSWORD no están "
                "definidas — no se crea ningún usuario."
            )
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True},
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        accion = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(f"Usuario '{username}' {accion} como superusuario.")
        )
