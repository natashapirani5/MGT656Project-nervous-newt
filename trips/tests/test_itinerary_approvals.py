"""#28: the organizer approves or rejects proposals."""

import datetime
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from trips.models import ItineraryItem, Membership, Trip

START = datetime.date(2027, 6, 10)
END = datetime.date(2027, 6, 13)
Kind = ItineraryItem.Kind
Status = ItineraryItem.Status


class ApprovalTestBase(TestCase):
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
            location="Graça",
            status=Status.APPROVED,
            proposed_by=self.organizer,
        )
        self.add = ItineraryItem.objects.create(
            trip=self.trip,
            title="Fado night",
            date=START + datetime.timedelta(days=1),
            time=datetime.time(21, 0),
            proposed_by=self.participant,
        )
        self.edit = ItineraryItem.objects.create(
            trip=self.trip,
            kind=Kind.EDIT,
            target=self.item,
            title="Tram 28 at sunrise",
            date=START + datetime.timedelta(days=2),
            time=datetime.time(6, 30),
            location="Martim Moniz",
            notes="Fewer crowds",
            proposed_by=self.participant,
        )
        self.remove = ItineraryItem.objects.create(
            trip=self.trip,
            kind=Kind.REMOVE,
            target=self.item,
            title="Tram 28",
            date=START,
            notes="Too touristy",
            proposed_by=self.participant,
        )
        self.detail_url = reverse("trip_detail", args=[self.trip.pk])

    def approve_url(self, proposal):
        return reverse("proposal_approve", args=[self.trip.pk, proposal.pk])

    def reject_url(self, proposal):
        return reverse("proposal_reject", args=[self.trip.pk, proposal.pk])

    def exists(self, obj):
        return ItineraryItem.objects.filter(pk=obj.pk).exists()


class ApproveTests(ApprovalTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.organizer)

    def test_approving_new_item_adds_it_to_the_itinerary(self):
        page = self.client.post(self.approve_url(self.add), follow=True)
        self.assertRedirects(page, self.detail_url)
        self.add.refresh_from_db()
        self.assertEqual(self.add.status, Status.APPROVED)
        self.assertEqual(self.add.proposed_by, self.participant)
        self.assertContains(page, "Approved: added “Fado night”")
        self.assertNotContains(page, "Suggested by")

    def test_approving_change_updates_the_item_and_clears_the_proposal(self):
        self.client.post(self.approve_url(self.edit))
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28 at sunrise")
        self.assertEqual(self.item.date, START + datetime.timedelta(days=2))
        self.assertEqual(self.item.time, datetime.time(6, 30))
        self.assertEqual(self.item.location, "Martim Moniz")
        self.assertEqual(self.item.notes, "Fewer crowds")
        self.assertEqual(self.item.status, Status.APPROVED)
        self.assertFalse(self.exists(self.edit))
        # Other pending proposals about the item are untouched.
        self.assertTrue(self.exists(self.remove))

    def test_approving_removal_deletes_the_item_and_proposals_about_it(self):
        self.client.post(self.approve_url(self.remove))
        self.assertFalse(self.exists(self.item))
        self.assertFalse(self.exists(self.remove))
        self.assertFalse(self.exists(self.edit))
        self.assertTrue(self.exists(self.add))
        self.assertContains(self.client.get(self.detail_url), "Approved: removed “Tram 28”")

    def test_cannot_approve_a_proposal_now_outside_the_trip_dates(self):
        self.trip.end_date = START  # the organizer shortened the trip after the suggestion
        self.trip.save()
        for proposal in (self.add, self.edit):
            response = self.client.post(self.approve_url(proposal), follow=True)
            self.assertContains(response, "outside the trip dates")
        self.add.refresh_from_db()
        self.assertEqual(self.add.status, Status.PROPOSED)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")

    def test_removal_can_be_approved_even_if_item_is_outside_new_dates(self):
        self.item.date = START
        self.item.save()
        self.trip.start_date = START + datetime.timedelta(days=1)
        self.trip.save()
        self.client.post(self.approve_url(self.remove))
        self.assertFalse(self.exists(self.item))

    def test_approved_items_cannot_be_approved_or_rejected_again(self):
        for url in (self.approve_url(self.item), self.reject_url(self.item)):
            self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(self.exists(self.item))

    def test_needs_post(self):
        self.assertEqual(self.client.get(self.approve_url(self.add)).status_code, 405)
        self.assertEqual(self.client.get(self.reject_url(self.add)).status_code, 405)
        self.add.refresh_from_db()
        self.assertEqual(self.add.status, Status.PROPOSED)


class RejectTests(ApprovalTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.organizer)

    def test_rejecting_each_kind_discards_it_and_leaves_itinerary_alone(self):
        for proposal in (self.add, self.edit, self.remove):
            response = self.client.post(self.reject_url(proposal))
            self.assertRedirects(response, self.detail_url)
            self.assertFalse(self.exists(proposal))
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")
        self.assertEqual(self.item.time, datetime.time(10, 0))
        self.assertEqual(ItineraryItem.objects.count(), 1)


class ReviewPermissionTests(ApprovalTestBase):
    def all_urls(self):
        for proposal in (self.add, self.edit, self.remove):
            yield self.approve_url(proposal)
            yield self.reject_url(proposal)

    def assert_nothing_changed(self):
        self.assertEqual(ItineraryItem.objects.count(), 4)
        self.add.refresh_from_db()
        self.assertEqual(self.add.status, Status.PROPOSED)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")

    def test_participant_gets_error_page(self):
        self.client.force_login(self.participant)
        for url in self.all_urls():
            self.assertEqual(self.client.post(url).status_code, 403, url)
        self.assert_nothing_changed()

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        for url in self.all_urls():
            self.assertEqual(self.client.post(url).status_code, 404, url)
        self.assert_nothing_changed()

    def test_requires_login(self):
        for url in self.all_urls():
            response = self.client.post(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")
        self.assert_nothing_changed()

    def test_proposal_from_another_trip_is_not_found(self):
        other = Trip.objects.create(organizer=self.organizer, destination="Porto")
        Membership.objects.create(trip=other, user=self.organizer, role=Membership.Role.ORGANIZER)
        self.client.force_login(self.organizer)
        url = reverse("proposal_approve", args=[other.pk, self.add.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assert_nothing_changed()


class TripPageReviewTests(ApprovalTestBase):
    def test_organizer_sees_every_pending_proposal_with_buttons_and_count(self):
        self.client.force_login(self.organizer)
        page = self.client.get(self.detail_url)
        self.assertContains(page, "3 suggestions waiting for your review")
        for proposal in (self.add, self.edit, self.remove):
            self.assertContains(page, f'action="{self.approve_url(proposal)}"')
            self.assertContains(page, f'action="{self.reject_url(proposal)}"')
        # Approved items get Edit/Remove, not Approve/Reject.
        self.assertNotContains(page, f'action="{self.approve_url(self.item)}"')

    def test_participant_sees_no_review_buttons_or_count(self):
        self.client.force_login(self.participant)
        page = self.client.get(self.detail_url)
        self.assertNotContains(page, "waiting for your review")
        for proposal in (self.add, self.edit, self.remove):
            self.assertNotContains(page, self.approve_url(proposal))
            self.assertNotContains(page, self.reject_url(proposal))

    def test_no_count_when_nothing_is_pending(self):
        ItineraryItem.objects.filter(status=Status.PROPOSED).delete()
        self.client.force_login(self.organizer)
        self.assertNotContains(self.client.get(self.detail_url), "waiting for your review")


class SeededProposalTests(TestCase):
    def test_grader_organizer_can_approve_each_seeded_proposal(self):
        call_command("seed", stdout=StringIO())
        organizer = User.objects.get(username="admin@example.com")
        trip = Trip.objects.get()
        proposals = list(ItineraryItem.objects.filter(status=Status.PROPOSED))
        self.assertEqual(len(proposals), 3)
        self.client.force_login(organizer)
        for proposal in proposals:
            url = reverse("proposal_approve", args=[trip.pk, proposal.pk])
            self.assertRedirects(self.client.post(url), reverse("trip_detail", args=[trip.pk]))
        self.assertFalse(ItineraryItem.objects.filter(status=Status.PROPOSED).exists())
        titles = set(ItineraryItem.objects.values_list("title", flat=True))
        self.assertIn("Late-night poutine at La Banquise", titles)
        self.assertNotIn("Vintage shopping on Saint-Laurent", titles)
        dinner = ItineraryItem.objects.get(title="Dinner at a bistro")
        self.assertEqual(dinner.time, datetime.time(20, 30))
