from django.urls import path

from . import views

urlpatterns = [
    path(f"{views.AB_HASH}", views.ab_page, name="ab_page"),
    path(f"{views.AB_HASH}/click", views.ab_click, name="ab_click"),
    path(f"{views.AB_HASH}/stats", views.ab_stats, name="ab_stats"),
]
