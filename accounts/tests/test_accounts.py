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
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Trip.objects.count(), 1)
        self.assertEqual(Membership.objects.count(), 2)
        self.assertEqual(ItineraryItem.objects.count(), 5)
        trip = Trip.objects.get()
        organizer = User.objects.get(username="admin@example.com")
        participant = User.objects.get(username="member@example.com")
        self.assertTrue(trip.is_organizer(organizer))
        self.assertTrue(trip.is_member(participant))
        self.assertFalse(trip.is_organizer(participant))

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
