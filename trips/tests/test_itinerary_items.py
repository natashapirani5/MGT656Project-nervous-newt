"""#26: the organizer adds, edits, and removes itinerary items."""

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from trips.models import ItineraryItem, Membership, Trip

START = datetime.date(2027, 6, 10)
END = datetime.date(2027, 6, 13)


class ItineraryItemTestBase(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user("org@example.com", password="pw-strong-123")
        self.participant = User.objects.create_user("part@example.com", password="pw-strong-123")
        self.outsider = User.objects.create_user("out@example.com", password="pw-strong-123")
        self.trip = Trip.objects.create(
            organizer=self.organizer, destination="Lisbon", start_date=START, end_date=END
        )
        Membership.objects.create(
            trip=self.trip, user=self.organizer, role=Membership.Role.ORGANIZER
        )
        Membership.objects.create(
            trip=self.trip, user=self.participant, role=Membership.Role.PARTICIPANT
        )
        self.item = ItineraryItem.objects.create(
            trip=self.trip,
            title="Tram 28",
            date=START,
            time=datetime.time(10, 0),
            status=ItineraryItem.Status.APPROVED,
            proposed_by=self.organizer,
        )
        self.detail_url = reverse("trip_detail", args=[self.trip.pk])
        self.add_url = reverse("item_add", args=[self.trip.pk])
        self.edit_url = reverse("item_edit", args=[self.trip.pk, self.item.pk])
        self.delete_url = reverse("item_delete", args=[self.trip.pk, self.item.pk])

    def valid_data(self, **overrides):
        data = {
            "title": "Pastéis de Belém",
            "date": "2027-06-11",
            "time": "15:30",
            "location": "Belém",
            "notes": "Get there before the line.",
        }
        data.update(overrides)
        return data


class AddItemTests(ItineraryItemTestBase):
    def test_organizer_adds_item_which_is_approved_straight_away(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.add_url, self.valid_data())
        self.assertRedirects(response, self.detail_url)
        item = ItineraryItem.objects.get(title="Pastéis de Belém")
        self.assertEqual(item.trip, self.trip)
        self.assertEqual(item.date, datetime.date(2027, 6, 11))
        self.assertEqual(item.time, datetime.time(15, 30))
        self.assertEqual(item.location, "Belém")
        self.assertEqual(item.notes, "Get there before the line.")
        self.assertEqual(item.status, ItineraryItem.Status.APPROVED)
        self.assertEqual(item.proposed_by, self.organizer)
        page = self.client.get(self.detail_url)
        self.assertContains(page, "Pastéis de Belém")
        self.assertNotContains(page, ">proposed<")

    def test_only_title_and_date_are_required(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.add_url, {"title": "Free day", "date": "2027-06-12"})
        self.assertRedirects(response, self.detail_url)
        item = ItineraryItem.objects.get(title="Free day")
        self.assertIsNone(item.time)
        self.assertEqual(item.location, "")

    def test_title_is_required(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.add_url, self.valid_data(title="   "))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a title.")
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_date_is_required(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.add_url, self.valid_data(date=""))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please pick a date.")
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_date_must_be_within_trip_dates(self):
        self.client.force_login(self.organizer)
        for bad in ("2027-06-09", "2027-06-14"):
            response = self.client.post(self.add_url, self.valid_data(date=bad))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "during the trip")
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_first_and_last_trip_days_are_allowed(self):
        self.client.force_login(self.organizer)
        self.client.post(self.add_url, self.valid_data(title="Arrive", date="2027-06-10"))
        self.client.post(self.add_url, self.valid_data(title="Leave", date="2027-06-13"))
        self.assertTrue(ItineraryItem.objects.filter(title="Arrive").exists())
        self.assertTrue(ItineraryItem.objects.filter(title="Leave").exists())

    def test_any_date_allowed_when_trip_has_no_dates(self):
        self.trip.start_date = self.trip.end_date = None
        self.trip.save()
        self.client.force_login(self.organizer)
        self.client.post(self.add_url, self.valid_data(date="2030-01-01"))
        self.assertTrue(ItineraryItem.objects.filter(date=datetime.date(2030, 1, 1)).exists())

    def test_date_picker_is_limited_to_trip_dates(self):
        self.client.force_login(self.organizer)
        response = self.client.get(self.add_url)
        self.assertContains(response, 'min="2027-06-10"')
        self.assertContains(response, 'max="2027-06-13"')

    def test_participant_cannot_add(self):
        self.client.force_login(self.participant)
        self.assertEqual(self.client.get(self.add_url).status_code, 403)
        response = self.client.post(self.add_url, self.valid_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        response = self.client.post(self.add_url, self.valid_data())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_requires_login(self):
        response = self.client.post(self.add_url, self.valid_data())
        self.assertRedirects(response, f"{reverse('login')}?next={self.add_url}")
        self.assertEqual(ItineraryItem.objects.count(), 1)


class EditItemTests(ItineraryItemTestBase):
    def test_organizer_edits_item(self):
        self.client.force_login(self.organizer)
        response = self.client.get(self.edit_url)
        self.assertContains(response, 'value="Tram 28"')
        response = self.client.post(
            self.edit_url, self.valid_data(title="Tram 28 (early)", date="2027-06-12")
        )
        self.assertRedirects(response, self.detail_url)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28 (early)")
        self.assertEqual(self.item.date, datetime.date(2027, 6, 12))

    def test_organizer_can_edit_a_participants_proposal(self):
        proposal = ItineraryItem.objects.create(
            trip=self.trip, title="Fado night", date=START, proposed_by=self.participant
        )
        self.client.force_login(self.organizer)
        url = reverse("item_edit", args=[self.trip.pk, proposal.pk])
        self.client.post(url, self.valid_data(title="Fado night in Alfama"))
        proposal.refresh_from_db()
        self.assertEqual(proposal.title, "Fado night in Alfama")
        # Editing doesn't approve it; approving proposals is #28.
        self.assertEqual(proposal.status, ItineraryItem.Status.PROPOSED)

    def test_edit_rejects_date_outside_trip(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.edit_url, self.valid_data(date="2027-07-01"))
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.date, START)

    def test_participant_cannot_edit(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.edit_url, self.valid_data(title="Hijacked"))
        self.assertEqual(response.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.edit_url).status_code, 404)

    def test_item_from_another_trip_is_not_found(self):
        other = Trip.objects.create(organizer=self.organizer, destination="Porto")
        Membership.objects.create(trip=other, user=self.organizer, role=Membership.Role.ORGANIZER)
        self.client.force_login(self.organizer)
        url = reverse("item_edit", args=[other.pk, self.item.pk])
        self.assertEqual(self.client.post(url, self.valid_data()).status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")


class DeleteItemTests(ItineraryItemTestBase):
    def test_get_shows_confirmation_and_does_not_delete(self):
        self.client.force_login(self.organizer)
        response = self.client.get(self.delete_url)
        self.assertContains(response, "Remove this item?")
        self.assertTrue(ItineraryItem.objects.filter(pk=self.item.pk).exists())

    def test_organizer_removes_item(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.detail_url)
        self.assertFalse(ItineraryItem.objects.filter(pk=self.item.pk).exists())
        self.assertNotContains(self.client.get(self.detail_url), "Tram 28")

    def test_participant_cannot_remove(self):
        self.client.force_login(self.participant)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(ItineraryItem.objects.filter(pk=self.item.pk).exists())

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.delete_url).status_code, 404)
        self.assertTrue(ItineraryItem.objects.filter(pk=self.item.pk).exists())


class TripPageButtonsTests(ItineraryItemTestBase):
    def test_organizer_sees_add_edit_remove(self):
        self.client.force_login(self.organizer)
        page = self.client.get(self.detail_url)
        self.assertContains(page, f'href="{self.add_url}"')
        self.assertContains(page, f'href="{self.edit_url}"')
        self.assertContains(page, f'href="{self.delete_url}"')

    def test_participant_does_not_see_them(self):
        self.client.force_login(self.participant)
        page = self.client.get(self.detail_url)
        self.assertContains(page, "Tram 28")
        self.assertNotContains(page, self.add_url)
        self.assertNotContains(page, self.edit_url)
        self.assertNotContains(page, self.delete_url)
