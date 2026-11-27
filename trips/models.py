import datetime

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

    def covers(self, date):
        """True if `date` falls within the trip's dates (or the trip has no dates set)."""
        if self.start_date and date < self.start_date:
            return False
        return not (self.end_date and date > self.end_date)


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
    """One itinerary entry, or a participant's proposal.

    - kind=ADD: an item in the itinerary (approved) or a proposed new item (proposed).
    - kind=EDIT: a proposed change to `target`; its fields hold the proposed new values.
    - kind=REMOVE: a proposal to remove `target`; its fields copy the target for display.
    EDIT and REMOVE rows are always proposals and never appear in the itinerary themselves.
    """

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        APPROVED = "approved", "Approved"

    class Kind(models.TextChoices):
        ADD = "add", "New item"
        EDIT = "edit", "Change"
        REMOVE = "remove", "Removal"

    COMPARED_FIELDS = ("title", "date", "time", "location", "notes")

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
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.ADD)
    # The approved item an EDIT or REMOVE proposal is about. If that item is removed,
    # proposals about it go too.
    target = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="change_proposals",
    )

    class Meta:
        ordering = ["date", "time", "id"]

    def __str__(self):
        return f"{self.date}: {self.title}"

    @property
    def is_proposal(self):
        return self.status == self.Status.PROPOSED

    def changes(self):
        """For an EDIT proposal: [(label, old, new)] as display text, one per changed field."""
        if self.kind != self.Kind.EDIT or self.target is None:
            return []
        diffs = []
        for name in self.COMPARED_FIELDS:
            old, new = getattr(self.target, name), getattr(self, name)
            if old != new:
                label = self._meta.get_field(name).verbose_name.capitalize()
                diffs.append((label, _display(old), _display(new)))
        return diffs


def _display(value):
    """Short, human-friendly text for an itinerary field value."""
    if value in (None, ""):
        return "(none)"
    if isinstance(value, datetime.date):
        return f"{value:%a, %b} {value.day}"
    if isinstance(value, datetime.time):
        return f"{value.hour % 12 or 12}:{value:%M %p}"
    return str(value)
