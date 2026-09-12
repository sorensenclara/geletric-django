from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.GeletricLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="core:login"), name="logout"),
    path("componentes/wizard/", views.wizard_demo, name="wizard_demo"),
    path("modulos/asociados/listado/", views.asociados_list, name="asociados_list"),
    path("modulos/asociados/ficha/<str:numero_asociado>/", views.asociado_ficha, name="asociado_ficha"),
    path("modulos/asociados/<slug:subslug>/", views.asociado_sub, name="asociado_sub"),
    path("modulos/<slug:slug>/", views.module_detail, name="module_detail"),
]
