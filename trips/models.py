from django.conf import settings
from django.db import models


class Trip(models.Model):
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organized_trips"
    )
    destination = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date", "destination"]

    def __str__(self):
        return self.destination

    def is_organizer(self, user):
        return self.memberships.filter(user=user, role=Membership.Role.ORGANIZER).exists()

    def is_member(self, user):
        return self.memberships.filter(user=user).exists()


class Membership(models.Model):
    """A user's role and RSVP on one trip. Roles are per trip."""

    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        PARTICIPANT = "participant", "Participant"

    class Rsvp(models.TextChoices):
        PENDING = "pending", "Pending"
        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe (with conditions)"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trip_memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    rsvp = models.CharField(max_length=20, choices=Rsvp.choices, default=Rsvp.PENDING)
    rsvp_condition = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["trip", "user"], name="unique_trip_member")]

    def __str__(self):
        return f"{self.user} on {self.trip} ({self.role})"


class ItineraryItem(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="itinerary_items")
    title = models.CharField(max_length=200)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["date", "time", "id"]

    def __str__(self):
        return f"{self.date}: {self.title}"
