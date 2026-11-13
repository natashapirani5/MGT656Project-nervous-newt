from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import TemplateView


def healthz(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("trips/", include("trips.urls")),
    path("", include("abtest.urls")),
]
