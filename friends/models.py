from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q


class Friendship(models.Model):
    """A friend request from one user to another; once accepted, they are friends.

    One row per pair of users (in either direction). Declining a request or
    removing a friend deletes the row.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="friend_requests_sent"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received",
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["from_user", "to_user"], name="unique_friend_request"),
            models.CheckConstraint(condition=~Q(from_user=F("to_user")), name="no_self_friendship"),
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"

    @classmethod
    def between(cls, a, b):
        """The row linking two users in either direction, or None."""
        return cls.objects.filter(Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)).first()


def friends_of(user):
    """QuerySet of users who are accepted friends of `user`. Used by trip invites (#15)."""
    accepted = Friendship.objects.filter(status=Friendship.Status.ACCEPTED)
    sent = accepted.filter(from_user=user).values("to_user")
    received = accepted.filter(to_user=user).values("from_user")
    return get_user_model().objects.filter(Q(pk__in=sent) | Q(pk__in=received))


def are_friends(a, b):
    row = Friendship.between(a, b)
    return row is not None and row.status == Friendship.Status.ACCEPTED
