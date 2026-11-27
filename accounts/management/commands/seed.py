"""Idempotent demo data + grader accounts. Safe to run any number of times.

Accounts (fake data, passwords used nowhere else):
  organizer: admin@example.com
  participant: member@example.com
Passwords default to the values below; override with SEED_ORGANIZER_PASSWORD /
SEED_PARTICIPANT_PASSWORD if you want different ones per environment.
"""

import datetime
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from friends.models import Friendship
from trips.models import ItineraryItem, Membership, Trip

ORGANIZER_EMAIL = "admin@example.com"
PARTICIPANT_EMAIL = "member@example.com"
DEFAULT_ORGANIZER_PASSWORD = "Grader-Organizer-656"
DEFAULT_PARTICIPANT_PASSWORD = "Grader-Member-656"
SEED_TRIP_DESTINATION = "Montreal, Canada"

# Demo travelers (no usable password; they exist so graders can search and get requests).
DEMO_TRAVELERS = [
    ("sam.rivera@example.com", "Sam Rivera", "Chicago, IL", "street food, cycling"),
    ("priya.shah@example.com", "Priya Shah", "Austin, TX", "live music, hot springs"),
    ("jordan.lee@example.com", "Jordan Lee", "Seattle, WA", "hiking, coffee"),
]


def upsert_first(model, lookup, values):
    """Update the oldest row matching `lookup` with `values`, or create one.

    Unlike update_or_create, this never fails when graders have since made more rows that
    match (e.g. the organizer added a second item with a seeded title). The seed runs on
    every deploy, so it must not crash on real data.
    """
    row = model.objects.filter(**lookup).order_by("pk").first()
    if row is None:
        return model.objects.create(**lookup, **values)
    for name, value in values.items():
        setattr(row, name, value)
    row.save()
    return row


def create_if_missing(model, lookup, values):
    """Create a row unless one matching `lookup` exists. Never fails on duplicates."""
    row = model.objects.filter(**lookup).order_by("pk").first()
    return row or model.objects.create(**lookup, **values)


def upsert_user(email, password, name, profile_fields, is_staff=False):
    user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
    user.email = email
    user.first_name = name
    user.is_staff = is_staff
    user.is_superuser = is_staff
    user.set_password(password)
    user.save()
    Profile.objects.update_or_create(user=user, defaults={"display_name": name, **profile_fields})
    return user


class Command(BaseCommand):
    help = "Create demo data and grader accounts (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        organizer = upsert_user(
            ORGANIZER_EMAIL,
            os.environ.get("SEED_ORGANIZER_PASSWORD", DEFAULT_ORGANIZER_PASSWORD),
            "Olive Organizer",
            {
                "home_city": "New Haven, CT",
                "interests": "food tours, vintage shopping, hiking",
                "wishlist_destinations": "Montreal, Lisbon, Kyoto",
                "trip_preferences": "splurges on food, prefers boutique hotels",
            },
            is_staff=True,
        )
        participant = upsert_user(
            PARTICIPANT_EMAIL,
            os.environ.get("SEED_PARTICIPANT_PASSWORD", DEFAULT_PARTICIPANT_PASSWORD),
            "Max Member",
            {
                "home_city": "Boston, MA",
                "interests": "museums, live music, scuba diving",
                "wishlist_destinations": "Montreal, Mexico City",
                "trip_preferences": "budget-conscious, prefers hostels",
            },
        )

        start = timezone.localdate() + datetime.timedelta(days=30)
        # The organizer can create trips (#15), so there may be another "Montreal, Canada".
        trip = upsert_first(
            Trip,
            lookup={"organizer": organizer, "destination": SEED_TRIP_DESTINATION},
            values={
                "description": "A relaxing long weekend with great food and vintage shopping.",
                "start_date": start,
                "end_date": start + datetime.timedelta(days=3),
                "budget": 1200,
            },
        )
        Membership.objects.update_or_create(
            trip=trip,
            user=organizer,
            defaults={"role": Membership.Role.ORGANIZER, "rsvp": Membership.Rsvp.YES},
        )
        Membership.objects.update_or_create(
            trip=trip,
            user=participant,
            defaults={
                "role": Membership.Role.PARTICIPANT,
                "rsvp": Membership.Rsvp.MAYBE,
                "rsvp_condition": "If we stay under $300/night",
            },
        )

        items = [
            (0, datetime.time(15, 0), "Check in & walk Old Montreal", "Old Montreal"),
            (0, datetime.time(19, 30), "Dinner at a bistro", "Plateau Mont-Royal"),
            (1, datetime.time(9, 0), "Jean-Talon Market breakfast", "Jean-Talon Market"),
            (
                1,
                datetime.time(13, 0),
                "Vintage shopping on Saint-Laurent",
                "Boulevard Saint-Laurent",
            ),
            (2, datetime.time(10, 0), "Hike up Mount Royal", "Mount Royal Park"),
        ]
        seeded = {}
        for offset, time, title, location in items:
            seeded[title] = upsert_first(
                ItineraryItem,
                lookup={
                    "trip": trip,
                    "title": title,
                    "kind": ItineraryItem.Kind.ADD,
                    "proposed_by": organizer,
                },
                values={
                    "date": start + datetime.timedelta(days=offset),
                    "time": time,
                    "location": location,
                    "status": ItineraryItem.Status.APPROVED,
                },
            )

        self.seed_proposals(trip, participant, start, seeded["Dinner at a bistro"])
        self.seed_friends(organizer, participant)
        self.stdout.write(self.style.SUCCESS("Seed data is in place."))

    def seed_proposals(self, trip, participant, start, dinner):
        """Pending suggestions from the grader participant (#27), for the organizer to review.

        Looked up without their status, so re-seeding never undoes an organizer's decision
        on them (except a rejected one, which comes back so the feature can be tried again).
        Graders may add their own matching suggestions, so these never fail on duplicates.
        """
        create_if_missing(
            ItineraryItem,
            lookup={
                "trip": trip,
                "kind": ItineraryItem.Kind.ADD,
                "proposed_by": participant,
                "title": "Late-night poutine at La Banquise",
            },
            values={
                "date": start + datetime.timedelta(days=1),
                "time": datetime.time(22, 0),
                "location": "Plateau Mont-Royal",
                "status": ItineraryItem.Status.PROPOSED,
            },
        )
        create_if_missing(
            ItineraryItem,
            lookup={
                "trip": trip,
                "kind": ItineraryItem.Kind.EDIT,
                "target": dinner,
                "proposed_by": participant,
            },
            values={
                "title": dinner.title,
                "date": dinner.date,
                "time": datetime.time(20, 30),
                "location": dinner.location,
                "notes": dinner.notes,
                "status": ItineraryItem.Status.PROPOSED,
            },
        )

    def seed_friends(self, organizer, participant):
        demo = {}
        for email, name, city, interests in DEMO_TRAVELERS:
            user, created = User.objects.get_or_create(
                username=email, defaults={"email": email, "first_name": name}
            )
            if created:
                user.set_unusable_password()
                user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={"display_name": name, "home_city": city, "interests": interests},
            )
            demo[email] = user

        # The two grader accounts are always friends.
        row = Friendship.between(organizer, participant)
        if row is None:
            row = Friendship(from_user=organizer, to_user=participant)
        if row.status != Friendship.Status.ACCEPTED:
            row.status = Friendship.Status.ACCEPTED
            row.accepted_at = timezone.now()
            row.save()

        # Pending requests graders can accept or decline. Only created when the pair has
        # no relationship yet, so re-seeding never undoes what a grader did (except a
        # declined request, which comes back so the feature can be tried again).
        for sender_email, recipient in [
            ("sam.rivera@example.com", organizer),
            ("priya.shah@example.com", participant),
        ]:
            sender = demo[sender_email]
            if Friendship.between(sender, recipient) is None:
                Friendship.objects.create(from_user=sender, to_user=recipient)

        # A friend of the organizer who isn't on the seeded trip yet, so graders can try
        # trip invites (#15) right away. Like above, only created if the pair has no row.
        jordan = demo["jordan.lee@example.com"]
        if Friendship.between(organizer, jordan) is None:
            Friendship.objects.create(
                from_user=organizer,
                to_user=jordan,
                status=Friendship.Status.ACCEPTED,
                accepted_at=timezone.now(),
            )
