from django.urls import path

from . import views

urlpatterns = [
    path("", views.friends_home, name="friends"),
    path("request/<int:user_id>/", views.send_request, name="friend_request_send"),
    path("requests/<int:pk>/accept/", views.accept_request, name="friend_request_accept"),
    path("requests/<int:pk>/decline/", views.decline_request, name="friend_request_decline"),
    path("<int:user_id>/remove/", views.remove_friend, name="friend_remove"),
]
