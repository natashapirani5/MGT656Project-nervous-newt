import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from trips.models import ItineraryItem, Membership, Trip


class TripViewTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user("org@example.com", password="pw-strong-123")
        self.member = User.objects.create_user("mem@example.com", password="pw-strong-123")
        self.outsider = User.objects.create_user("out@example.com", password="pw-strong-123")
        start = timezone.localdate() + datetime.timedelta(days=10)
        self.trip = Trip.objects.create(
            organizer=self.organizer,
            destination="Lisbon",
            start_date=start,
            end_date=start + datetime.timedelta(days=2),
        )
        Membership.objects.create(
            trip=self.trip, user=self.organizer, role=Membership.Role.ORGANIZER
        )
        Membership.objects.create(trip=self.trip, user=self.member)
        ItineraryItem.objects.create(trip=self.trip, title="Tram 28", date=start)
        past = timezone.localdate() - datetime.timedelta(days=30)
        self.past_trip = Trip.objects.create(
            organizer=self.organizer,
            destination="Past Place",
            start_date=past,
            end_date=past + datetime.timedelta(days=1),
        )
        Membership.objects.create(
            trip=self.past_trip, user=self.organizer, role=Membership.Role.ORGANIZER
        )

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_dashboard_shows_only_my_upcoming_trips(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Lisbon")
        self.assertNotContains(response, "Past Place")

        self.client.force_login(self.outsider)
        self.assertNotContains(self.client.get(reverse("dashboard")), "Lisbon")

    def test_members_can_view_trip(self):
        for user in (self.organizer, self.member):
            self.client.force_login(user)
            response = self.client.get(reverse("trip_detail", args=[self.trip.pk]))
            self.assertContains(response, "Tram 28")

    def test_organizer_badge_only_for_organizer(self):
        self.client.force_login(self.organizer)
        url = reverse("trip_detail", args=[self.trip.pk])
        self.assertContains(self.client.get(url), "the organizer</span>")
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(url), "the organizer</span>")

    def test_non_member_cannot_view_trip(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("trip_detail", args=[self.trip.pk]))
        self.assertEqual(response.status_code, 404)


class HealthTests(TestCase):
    def test_healthz(self):
        self.assertEqual(self.client.get("/healthz").json(), {"status": "ok"})

    def test_home(self):
        self.assertEqual(self.client.get("/").status_code, 200)
