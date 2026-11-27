"""#27: participants propose new items, changes, and removals."""

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from trips.models import ItineraryItem, Membership, Trip

START = datetime.date(2027, 6, 10)
END = datetime.date(2027, 6, 13)
Kind = ItineraryItem.Kind
Status = ItineraryItem.Status


class ProposalTestBase(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user("org@example.com", password="pw-strong-123")
        self.participant = User.objects.create_user("part@example.com", password="pw-strong-123")
        Profile.objects.create(user=self.participant, display_name="Max Member")
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
        self.detail_url = reverse("trip_detail", args=[self.trip.pk])
        self.add_url = reverse("propose_add", args=[self.trip.pk])
        self.edit_url = reverse("propose_edit", args=[self.trip.pk, self.item.pk])
        self.remove_url = reverse("propose_remove", args=[self.trip.pk, self.item.pk])

    def item_data(self, **overrides):
        data = {
            "title": "Tram 28",
            "date": "2027-06-10",
            "time": "10:00",
            "location": "Graça",
            "notes": "",
        }
        data.update(overrides)
        return data

    def assert_itinerary_unchanged(self):
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Tram 28")
        self.assertEqual(self.item.time, datetime.time(10, 0))
        self.assertEqual(self.item.status, Status.APPROVED)
        self.assertEqual(ItineraryItem.objects.filter(status=Status.APPROVED).count(), 1)


class ProposeNewItemTests(ProposalTestBase):
    def test_participant_proposes_new_item(self):
        self.client.force_login(self.participant)
        response = self.client.post(
            self.add_url, self.item_data(title="Fado night", date="2027-06-11", time="21:00")
        )
        self.assertRedirects(response, self.detail_url)
        proposal = ItineraryItem.objects.get(title="Fado night")
        self.assertEqual(proposal.kind, Kind.ADD)
        self.assertEqual(proposal.status, Status.PROPOSED)
        self.assertEqual(proposal.proposed_by, self.participant)
        self.assert_itinerary_unchanged()

    def test_new_item_proposal_shows_as_proposed_with_name(self):
        ItineraryItem.objects.create(
            trip=self.trip, title="Fado night", date=START, proposed_by=self.participant
        )
        self.client.force_login(self.organizer)
        page = self.client.get(self.detail_url)
        self.assertContains(page, "Fado night")
        self.assertContains(page, ">proposed<")
        self.assertContains(page, "Suggested by Max Member")

    def test_proposal_must_be_within_trip_dates(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.add_url, self.item_data(date="2027-07-01"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "during the trip")
        self.assertFalse(ItineraryItem.objects.filter(status=Status.PROPOSED).exists())


class ProposeChangeTests(ProposalTestBase):
    def test_form_starts_with_current_values(self):
        self.client.force_login(self.participant)
        response = self.client.get(self.edit_url)
        self.assertContains(response, 'value="Tram 28"')
        self.assertContains(response, 'value="Graça"')

    def test_participant_proposes_change_without_changing_itinerary(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.edit_url, self.item_data(time="08:30"))
        self.assertRedirects(response, self.detail_url)
        proposal = ItineraryItem.objects.get(kind=Kind.EDIT)
        self.assertEqual(proposal.status, Status.PROPOSED)
        self.assertEqual(proposal.target, self.item)
        self.assertEqual(proposal.proposed_by, self.participant)
        self.assertEqual(proposal.time, datetime.time(8, 30))
        self.assertEqual(proposal.changes(), [("Time", "10:00 AM", "8:30 AM")])
        self.assert_itinerary_unchanged()

    def test_change_shows_under_the_item_with_name_and_differences(self):
        self.client.force_login(self.participant)
        self.client.post(self.edit_url, self.item_data(time="08:30", location="Alfama"))
        page = self.client.get(self.detail_url)
        self.assertContains(page, "suggested by Max Member")
        self.assertContains(page, "10:00 AM</s> &rarr; 8:30 AM")
        self.assertContains(page, "Graça</s> &rarr; Alfama")
        # The proposal isn't listed as an itinerary item of its own.
        self.assertContains(page, "<strong>Tram 28</strong>", count=1)

    def test_proposal_with_no_changes_is_rejected(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.edit_url, self.item_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You haven&#x27;t changed anything yet.")
        self.assertFalse(ItineraryItem.objects.filter(kind=Kind.EDIT).exists())

    def test_changed_date_must_be_within_trip(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.edit_url, self.item_data(date="2027-06-20"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ItineraryItem.objects.filter(kind=Kind.EDIT).exists())

    def test_cannot_propose_change_to_a_proposal(self):
        proposal = ItineraryItem.objects.create(
            trip=self.trip, title="Fado night", date=START, proposed_by=self.participant
        )
        self.client.force_login(self.participant)
        url = reverse("propose_edit", args=[self.trip.pk, proposal.pk])
        self.assertEqual(self.client.get(url).status_code, 404)


class ProposeRemovalTests(ProposalTestBase):
    def test_get_shows_confirmation_and_changes_nothing(self):
        self.client.force_login(self.participant)
        response = self.client.get(self.remove_url)
        self.assertContains(response, "Suggest removing this item?")
        self.assertFalse(ItineraryItem.objects.filter(kind=Kind.REMOVE).exists())

    def test_participant_proposes_removal_without_removing(self):
        self.client.force_login(self.participant)
        response = self.client.post(self.remove_url, {"reason": "Too touristy"})
        self.assertRedirects(response, self.detail_url)
        proposal = ItineraryItem.objects.get(kind=Kind.REMOVE)
        self.assertEqual(proposal.status, Status.PROPOSED)
        self.assertEqual(proposal.target, self.item)
        self.assertEqual(proposal.proposed_by, self.participant)
        self.assertEqual(proposal.notes, "Too touristy")
        self.assert_itinerary_unchanged()
        page = self.client.get(self.detail_url)
        self.assertContains(page, "Remove this item")
        self.assertContains(page, "suggested by Max Member")
        self.assertContains(page, "Too touristy")

    def test_reason_is_required(self):
        self.client.force_login(self.participant)
        for data in ({}, {"reason": "   "}):
            response = self.client.post(self.remove_url, data)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Please say why you&#x27;d remove it.")
        self.assertFalse(ItineraryItem.objects.filter(kind=Kind.REMOVE).exists())

    def test_same_person_cannot_propose_removal_twice(self):
        self.client.force_login(self.participant)
        self.client.post(self.remove_url, {"reason": "Too touristy"})
        self.client.post(self.remove_url, {"reason": "Still too touristy"})
        self.assertEqual(ItineraryItem.objects.filter(kind=Kind.REMOVE).count(), 1)

    def test_removing_the_item_also_removes_proposals_about_it(self):
        self.client.force_login(self.participant)
        self.client.post(self.remove_url, {"reason": "Too touristy"})
        self.client.post(self.edit_url, self.item_data(time="08:30"))
        self.item.delete()
        self.assertFalse(ItineraryItem.objects.exists())


class WithdrawTests(ProposalTestBase):
    def setUp(self):
        super().setUp()
        self.other = User.objects.create_user("other@example.com", password="pw-strong-123")
        Membership.objects.create(trip=self.trip, user=self.other)

    def make_proposal(self, by, **fields):
        defaults = {"trip": self.trip, "title": "Fado night", "date": START, "proposed_by": by}
        defaults.update(fields)
        return ItineraryItem.objects.create(**defaults)

    def withdraw_url(self, proposal):
        return reverse("proposal_withdraw", args=[self.trip.pk, proposal.pk])

    def test_participant_withdraws_each_kind_of_own_suggestion(self):
        proposals = [
            self.make_proposal(self.participant),
            self.make_proposal(self.participant, kind=Kind.EDIT, target=self.item),
            self.make_proposal(self.participant, kind=Kind.REMOVE, target=self.item),
        ]
        self.client.force_login(self.participant)
        for proposal in proposals:
            response = self.client.post(self.withdraw_url(proposal))
            self.assertRedirects(response, self.detail_url)
            self.assertFalse(ItineraryItem.objects.filter(pk=proposal.pk).exists())
        self.assert_itinerary_unchanged()

    def test_cannot_withdraw_someone_elses_suggestion(self):
        proposal = self.make_proposal(self.other)
        for user in (self.participant, self.organizer):
            self.client.force_login(user)
            self.assertEqual(self.client.post(self.withdraw_url(proposal)).status_code, 403)
        self.assertTrue(ItineraryItem.objects.filter(pk=proposal.pk).exists())

    def test_cannot_withdraw_an_approved_item(self):
        self.client.force_login(self.organizer)
        self.assertEqual(self.client.post(self.withdraw_url(self.item)).status_code, 404)
        self.assert_itinerary_unchanged()

    def test_withdraw_needs_post(self):
        proposal = self.make_proposal(self.participant)
        self.client.force_login(self.participant)
        self.assertEqual(self.client.get(self.withdraw_url(proposal)).status_code, 405)
        self.assertTrue(ItineraryItem.objects.filter(pk=proposal.pk).exists())

    def test_non_member_gets_not_found(self):
        proposal = self.make_proposal(self.participant)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(self.withdraw_url(proposal)).status_code, 404)

    def test_withdraw_button_only_on_own_suggestions(self):
        mine = self.make_proposal(self.participant, title="Mine")
        theirs = self.make_proposal(self.other, title="Theirs")
        mine_change = self.make_proposal(
            self.participant, kind=Kind.EDIT, target=self.item, title="Tram 28 (late)"
        )
        self.client.force_login(self.participant)
        page = self.client.get(self.detail_url)
        self.assertContains(page, f'action="{self.withdraw_url(mine)}"')
        self.assertContains(page, f'action="{self.withdraw_url(mine_change)}"')
        self.assertNotContains(page, f'action="{self.withdraw_url(theirs)}"')


class ProposalPermissionTests(ProposalTestBase):
    def urls(self):
        return [self.add_url, self.edit_url, self.remove_url]

    def test_organizer_cannot_propose(self):
        self.client.force_login(self.organizer)
        for url in self.urls():
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.client.post(self.add_url, self.item_data(title="Fado night"))
        self.assertFalse(ItineraryItem.objects.filter(status=Status.PROPOSED).exists())

    def test_non_member_gets_not_found(self):
        self.client.force_login(self.outsider)
        for url in self.urls():
            self.assertEqual(self.client.post(url, self.item_data()).status_code, 404, url)
        self.assertEqual(ItineraryItem.objects.count(), 1)

    def test_requires_login(self):
        for url in self.urls():
            response = self.client.post(url, self.item_data())
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_item_from_another_trip_is_not_found(self):
        other = Trip.objects.create(organizer=self.organizer, destination="Porto")
        Membership.objects.create(trip=other, user=self.participant)
        self.client.force_login(self.participant)
        url = reverse("propose_remove", args=[other.pk, self.item.pk])
        self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_participant_sees_suggest_links_not_organizer_controls(self):
        self.client.force_login(self.participant)
        page = self.client.get(self.detail_url)
        self.assertContains(page, f'href="{self.add_url}"')
        self.assertContains(page, f'href="{self.edit_url}"')
        self.assertContains(page, f'href="{self.remove_url}"')
        self.assertNotContains(page, reverse("item_add", args=[self.trip.pk]))

    def test_organizer_sees_controls_not_suggest_links(self):
        self.client.force_login(self.organizer)
        page = self.client.get(self.detail_url)
        self.assertNotContains(page, self.add_url)
        self.assertNotContains(page, self.edit_url)
        self.assertContains(page, reverse("item_add", args=[self.trip.pk]))

    def test_organizer_edit_and_delete_pages_ignore_change_proposals(self):
        proposal = ItineraryItem.objects.create(
            trip=self.trip,
            kind=Kind.REMOVE,
            target=self.item,
            title="Tram 28",
            date=START,
            proposed_by=self.participant,
        )
        self.client.force_login(self.organizer)
        for name in ("item_edit", "item_delete"):
            url = reverse(name, args=[self.trip.pk, proposal.pk])
            self.assertEqual(self.client.get(url).status_code, 404, name)
