"""
Formularios propios de GELETRIC.

GeletricLoginForm es un AuthenticationForm estándar de Django (misma
validación de usuario/contraseña de siempre): lo único que cambia son los
widgets, para que el <input> ya salga con la clase que usa el CSS del login
(ver .auth-input en dashboard.css) en vez del render por defecto de Django.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class GeletricLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "usuario@geletric.com.ar",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "auth-input",
            "placeholder": "••••••••",
        }),
    )
