from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<int:pk>/", views.trip_detail, name="trip_detail"),
]
