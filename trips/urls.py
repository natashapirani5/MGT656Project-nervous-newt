from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("new/", views.trip_create, name="trip_create"),
    path("<int:pk>/", views.trip_detail, name="trip_detail"),
    path("<int:pk>/edit/", views.trip_edit, name="trip_edit"),
    path("<int:pk>/invite/", views.trip_invite, name="trip_invite"),
    path("<int:pk>/items/new/", views.item_add, name="item_add"),
    path("<int:pk>/items/<int:item_pk>/edit/", views.item_edit, name="item_edit"),
    path("<int:pk>/items/<int:item_pk>/delete/", views.item_delete, name="item_delete"),
]
