import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from trips.forms import wishlist_destinations
from trips.models import Membership, Trip


def future(days):
    return timezone.localdate() + datetime.timedelta(days=days)


class TripCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("org@example.com", password="pw-strong-123")
        Profile.objects.create(user=self.user, wishlist_destinations="Lisbon, Kyoto\nMontreal")
        self.url = reverse("trip_create")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.client.post(self.url, {"destination": "Lisbon"})
        self.assertFalse(Trip.objects.exists())

    def test_dashboard_has_new_trip_button(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("dashboard")), f'href="{self.url}"')

    def test_form_suggests_wishlist_destinations(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, 'list="wishlist-destinations"')
        for place in ("Lisbon", "Kyoto", "Montreal"):
            self.assertContains(response, f'<option value="{place}">')

    def test_create_makes_creator_organizer_and_shows_on_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "destination": "  Lisbon  ",
                "start_date": future(10),
                "end_date": future(14),
                "description": "Pastéis and trams",
                "budget": "1500",
            },
        )
        trip = Trip.objects.get()
        self.assertRedirects(response, reverse("trip_detail", args=[trip.pk]))
        self.assertEqual(trip.destination, "Lisbon")
        self.assertEqual(trip.organizer, self.user)
        self.assertEqual(trip.budget, Decimal("1500"))
        membership = Membership.objects.get(trip=trip)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, Membership.Role.ORGANIZER)
        self.assertContains(self.client.get(reverse("dashboard")), "Lisbon")

    def test_any_destination_allowed_not_just_wishlist(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"destination": "Reykjavik"})
        self.assertEqual(Trip.objects.get().destination, "Reykjavik")

    def test_only_destination_is_required(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"destination": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Trip.objects.exists())
        response = self.client.post(self.url, {"destination": "Kyoto"})
        trip = Trip.objects.get()
        self.assertIsNone(trip.start_date)
        self.assertIsNone(trip.budget)

    def test_end_date_before_start_date_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {"destination": "Lisbon", "start_date": future(10), "end_date": future(5)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The end date can&#x27;t be before the start date.")
        self.assertFalse(Trip.objects.exists())

    def test_same_day_trip_is_allowed(self):
        self.client.force_login(self.user)
        self.client.post(
            self.url, {"destination": "Lisbon", "start_date": future(3), "end_date": future(3)}
        )
        self.assertTrue(Trip.objects.exists())

    def test_negative_budget_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"destination": "Lisbon", "budget": "-5"})
        self.assertContains(response, "Budget can&#x27;t be negative.")
        self.assertFalse(Trip.objects.exists())


class TripEditTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user("org@example.com", password="pw-strong-123")
        self.member = User.objects.create_user("mem@example.com", password="pw-strong-123")
        self.outsider = User.objects.create_user("out@example.com", password="pw-strong-123")
        self.trip = Trip.objects.create(
            organizer=self.organizer,
            destination="Lisbon",
            start_date=future(10),
            end_date=future(12),
        )
        Membership.objects.create(
            trip=self.trip, user=self.organizer, role=Membership.Role.ORGANIZER
        )
        Membership.objects.create(trip=self.trip, user=self.member)
        self.url = reverse("trip_edit", args=[self.trip.pk])
        self.new_details = {
            "destination": "Porto",
            "start_date": future(20),
            "end_date": future(23),
            "description": "Changed plans",
            "budget": "900",
        }

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_organizer_sees_edit_button_and_participant_does_not(self):
        detail = reverse("trip_detail", args=[self.trip.pk])
        self.client.force_login(self.organizer)
        self.assertContains(self.client.get(detail), f'href="{self.url}"')
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(detail), f'href="{self.url}"')

    def test_organizer_can_edit(self):
        self.client.force_login(self.organizer)
        form = self.client.get(self.url)
        self.assertContains(form, 'value="Lisbon"')
        response = self.client.post(self.url, self.new_details)
        self.assertRedirects(response, reverse("trip_detail", args=[self.trip.pk]))
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.destination, "Porto")
        self.assertEqual(self.trip.end_date, future(23))
        self.assertEqual(self.trip.budget, Decimal("900"))
        self.assertEqual(self.trip.memberships.count(), 2)

    def test_edit_rejects_end_before_start(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.url, {**self.new_details, "end_date": future(1)})
        self.assertContains(response, "The end date can&#x27;t be before the start date.")
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.destination, "Lisbon")

    def test_participant_gets_error_page_and_cannot_edit(self):
        self.client.force_login(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response, "Only the trip&#x27;s organizer can edit it.", status_code=403
        )
        response = self.client.post(self.url, self.new_details)
        self.assertEqual(response.status_code, 403)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.destination, "Lisbon")

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.new_details).status_code, 404)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.destination, "Lisbon")


class WishlistParsingTests(TestCase):
    def test_splits_and_dedupes(self):
        user = User.objects.create_user("w@example.com", password="pw-strong-123")
        Profile.objects.create(
            user=user, wishlist_destinations="Lisbon, kyoto;\n Lisbon ,, Mexico City\nKyoto"
        )
        self.assertEqual(wishlist_destinations(user), ["Lisbon", "kyoto", "Mexico City"])

    def test_user_without_profile(self):
        user = User.objects.create_user("np@example.com", password="pw-strong-123")
        self.assertEqual(wishlist_destinations(user), [])
