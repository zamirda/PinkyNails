from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("citas.urls")),
    # Fotos subidas desde el admin. Para un salón pequeño alcanza; en un sitio grande usa un almacenamiento externo.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
