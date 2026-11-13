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
from trips.models import ItineraryItem, Membership, Trip

ORGANIZER_EMAIL = "admin@example.com"
PARTICIPANT_EMAIL = "member@example.com"
DEFAULT_ORGANIZER_PASSWORD = "Grader-Organizer-656"
DEFAULT_PARTICIPANT_PASSWORD = "Grader-Member-656"
SEED_TRIP_DESTINATION = "Montreal, Canada"


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
        trip, _ = Trip.objects.update_or_create(
            organizer=organizer,
            destination=SEED_TRIP_DESTINATION,
            defaults={
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
        for offset, time, title, location in items:
            ItineraryItem.objects.update_or_create(
                trip=trip,
                title=title,
                defaults={
                    "date": start + datetime.timedelta(days=offset),
                    "time": time,
                    "location": location,
                    "status": ItineraryItem.Status.APPROVED,
                    "proposed_by": organizer,
                },
            )

        self.stdout.write(self.style.SUCCESS("Seed data is in place."))
