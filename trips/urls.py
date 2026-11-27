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
    path("<int:pk>/items/propose/", views.propose_add, name="propose_add"),
    path(
        "<int:pk>/items/<int:item_pk>/propose-change/",
        views.propose_edit,
        name="propose_edit",
    ),
    path(
        "<int:pk>/items/<int:item_pk>/propose-removal/",
        views.propose_remove,
        name="propose_remove",
    ),
    path(
        "<int:pk>/items/<int:item_pk>/withdraw/",
        views.proposal_withdraw,
        name="proposal_withdraw",
    ),
    path(
        "<int:pk>/items/<int:item_pk>/approve/",
        views.proposal_approve,
        name="proposal_approve",
    ),
    path(
        "<int:pk>/items/<int:item_pk>/reject/",
        views.proposal_reject,
        name="proposal_reject",
    ),
]
