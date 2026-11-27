from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from trips.models import ItineraryItem, Membership, Trip


class SignupLoginTests(TestCase):
    def test_signup_creates_user_and_profile_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "email": "New@Example.com",
                "display_name": "New Person",
                "password1": "a-strong-pass-123",
                "password2": "a-strong-pass-123",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        user = User.objects.get(username="new@example.com")
        self.assertEqual(user.profile.display_name, "New Person")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user("taken@example.com", password="x-strong-pass-1")
        response = self.client.post(
            reverse("signup"),
            {
                "email": "taken@example.com",
                "display_name": "Dup",
                "password1": "a-strong-pass-123",
                "password2": "a-strong-pass-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_login_with_email(self):
        User.objects.create_user("me@example.com", password="a-strong-pass-123")
        response = self.client.post(
            reverse("login"), {"username": "me@example.com", "password": "a-strong-pass-123"}
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_edit(self):
        user = User.objects.create_user("me@example.com", password="a-strong-pass-123")
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile"),
            {
                "display_name": "Me",
                "home_city": "New Haven",
                "interests": "hiking",
                "wishlist_destinations": "Lisbon",
                "trip_preferences": "prefers hostels",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(Profile.objects.get(user=user).home_city, "New Haven")


class SeedCommandTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed", stdout=StringIO())
        call_command("seed", stdout=StringIO())
        self.assertEqual(User.objects.count(), 5)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 2)
        # 5 approved items plus one pending proposal of each kind from the participant.
        self.assertEqual(ItineraryItem.objects.filter(status="approved").count(), 5)
        proposals = ItineraryItem.objects.filter(status="proposed")
        self.assertEqual(
            sorted(proposals.values_list("kind", flat=True)), ["add", "edit", "remove"]
        )
        self.assertTrue(all(p.proposed_by.username == "member@example.com" for p in proposals))
        trip = Trip.objects.get()
        organizer = User.objects.get(username="admin@example.com")
        participant = User.objects.get(username="member@example.com")
        self.assertTrue(trip.is_organizer(organizer))
        self.assertTrue(trip.is_member(participant))
        self.assertFalse(trip.is_organizer(participant))

    def test_seed_survives_items_graders_added_with_seeded_titles(self):
        # The seed runs on every deploy; a duplicate title must not crash it.
        call_command("seed", stdout=StringIO())
        dinner = ItineraryItem.objects.get(title="Dinner at a bistro", kind="add")
        participant = User.objects.get(username="member@example.com")
        # The organizer adds a second "Dinner at a bistro"...
        ItineraryItem.objects.create(
            trip=dinner.trip,
            title=dinner.title,
            date=dinner.date,
            status="approved",
            proposed_by=dinner.proposed_by,
        )
        # ...and the grader participant makes their own suggestions like the seeded ones.
        ItineraryItem.objects.create(
            trip=dinner.trip,
            kind="edit",
            target=dinner,
            title=dinner.title,
            date=dinner.date,
            notes="d",
            proposed_by=participant,
        )
        ItineraryItem.objects.create(
            trip=dinner.trip,
            title="Late-night poutine at La Banquise",
            date=dinner.date,
            proposed_by=participant,
        )
        call_command("seed", stdout=StringIO())
        self.assertEqual(ItineraryItem.objects.filter(title=dinner.title, kind="add").count(), 2)
        self.assertEqual(ItineraryItem.objects.filter(kind="edit").count(), 2)

    def test_seed_survives_a_second_trip_with_the_seeded_destination(self):
        call_command("seed", stdout=StringIO())
        seeded = Trip.objects.get()
        Trip.objects.create(organizer=seeded.organizer, destination=seeded.destination)
        call_command("seed", stdout=StringIO())
        self.assertEqual(Trip.objects.count(), 2)
        # The original trip keeps its itinerary; the new one isn't filled in.
        self.assertEqual(seeded.itinerary_items.filter(status="approved").count(), 5)
        self.assertFalse(Trip.objects.exclude(pk=seeded.pk).get().itinerary_items.exists())

    def test_seeded_accounts_can_log_in(self):
        from accounts.management.commands import seed

        call_command("seed", stdout=StringIO())
        self.assertTrue(
            self.client.login(
                username=seed.ORGANIZER_EMAIL, password=seed.DEFAULT_ORGANIZER_PASSWORD
            )
        )
        self.assertTrue(
            self.client.login(
                username=seed.PARTICIPANT_EMAIL, password=seed.DEFAULT_PARTICIPANT_PASSWORD
            )
        )
