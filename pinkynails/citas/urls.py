from django.urls import path

from . import views

app_name = "citas"

urlpatterns = [
    path("", views.index, name="index"),
    path("agendar/", views.agendar, name="agendar"),
    path("panel/", views.panel, name="panel"),
    path("panel/entrar/", views.entrar, name="login"),
    path("panel/salir/", views.salir, name="logout"),
    path("panel/cuenta/", views.cuenta, name="cuenta"),
]
