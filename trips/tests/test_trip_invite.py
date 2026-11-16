import datetime
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from friends.models import Friendship
from trips.models import Membership, Trip


def make_user(email, name):
    user = User.objects.create_user(email, email=email, password="pw-strong-123", first_name=name)
    Profile.objects.create(user=user, display_name=name)
    return user


def befriend(a, b, status=Friendship.Status.ACCEPTED):
    return Friendship.objects.create(from_user=a, to_user=b, status=status)


class TripInviteTests(TestCase):
    def setUp(self):
        self.organizer = make_user("org@example.com", "Olive")
        self.participant = make_user("mem@example.com", "Max")
        self.friend = make_user("fran@example.com", "Fran")
        self.friend2 = make_user("gus@example.com", "Gus")
        self.stranger = make_user("stan@example.com", "Stan")
        self.pending = make_user("pat@example.com", "Pat")
        self.outsider = make_user("out@example.com", "Otto")

        befriend(self.organizer, self.participant)
        befriend(self.friend, self.organizer)  # friendship works in either direction
        befriend(self.organizer, self.friend2)
        befriend(self.organizer, self.pending, status=Friendship.Status.PENDING)
        befriend(self.participant, self.stranger)  # a friend of the participant only

        start = timezone.localdate() + datetime.timedelta(days=10)
        self.trip = Trip.objects.create(
            organizer=self.organizer, destination="Lisbon", start_date=start, end_date=start
        )
        Membership.objects.create(
            trip=self.trip, user=self.organizer, role=Membership.Role.ORGANIZER
        )
        Membership.objects.create(trip=self.trip, user=self.participant)
        self.url = reverse("trip_invite", args=[self.trip.pk])
        self.detail = reverse("trip_detail", args=[self.trip.pk])

    def invite(self, *users):
        return self.client.post(self.url, {"friends": [u.pk for u in users]})

    def member_ids(self):
        return set(self.trip.memberships.values_list("user_id", flat=True))

    def test_requires_login(self):
        response = self.invite(self.friend)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.assertNotIn(self.friend.pk, self.member_ids())

    def test_get_not_allowed(self):
        self.client.force_login(self.organizer)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_organizer_sees_only_friends_not_on_trip(self):
        self.client.force_login(self.organizer)
        response = self.client.get(self.detail)
        invitable = list(response.context["invitable"])
        self.assertCountEqual(invitable, [self.friend, self.friend2])
        self.assertContains(response, f'action="{self.url}"')
        self.assertNotContains(response, "fran@example.com")  # names only, never emails

    def test_invite_one_or_more_friends_with_pending_rsvp(self):
        self.client.force_login(self.organizer)
        response = self.invite(self.friend, self.friend2)
        self.assertRedirects(response, self.detail, fetch_redirect_response=False)
        for user in (self.friend, self.friend2):
            membership = Membership.objects.get(trip=self.trip, user=user)
            self.assertEqual(membership.role, Membership.Role.PARTICIPANT)
            self.assertEqual(membership.rsvp, Membership.Rsvp.PENDING)
        page = self.client.get(self.detail)
        self.assertContains(page, "Invited Fran, Gus.")
        self.assertEqual(list(page.context["invitable"]), [])

    def test_invited_friend_can_see_trip_on_dashboard(self):
        self.client.force_login(self.organizer)
        self.invite(self.friend)
        self.client.force_login(self.friend)
        self.assertContains(self.client.get(reverse("dashboard")), "Lisbon")
        self.assertEqual(self.client.get(self.detail).status_code, 200)

    def test_cannot_invite_non_friend(self):
        self.client.force_login(self.organizer)
        for user in (self.stranger, self.pending):
            response = self.invite(user)
            self.assertRedirects(response, self.detail, fetch_redirect_response=False)
            self.assertNotIn(user.pk, self.member_ids())
        self.assertContains(self.client.get(self.detail), "You can only invite your friends.")

    def test_mixed_friend_and_non_friend_invites_nobody(self):
        self.client.force_login(self.organizer)
        self.invite(self.friend, self.stranger)
        self.assertEqual(self.member_ids(), {self.organizer.pk, self.participant.pk})

    def test_inviting_someone_already_on_trip_does_nothing(self):
        Membership.objects.filter(trip=self.trip, user=self.participant).update(
            rsvp=Membership.Rsvp.YES
        )
        self.client.force_login(self.organizer)
        response = self.invite(self.participant)
        self.assertRedirects(response, self.detail, fetch_redirect_response=False)
        self.assertEqual(self.trip.memberships.count(), 2)
        membership = Membership.objects.get(trip=self.trip, user=self.participant)
        self.assertEqual(membership.rsvp, Membership.Rsvp.YES)  # existing RSVP untouched
        self.assertContains(self.client.get(self.detail), "already on this trip")

        self.invite(self.friend)
        self.invite(self.friend)
        self.assertEqual(Membership.objects.filter(trip=self.trip, user=self.friend).count(), 1)

    def test_empty_invite_shows_error(self):
        self.client.force_login(self.organizer)
        response = self.client.post(self.url, {})
        self.assertRedirects(response, self.detail, fetch_redirect_response=False)
        self.assertContains(self.client.get(self.detail), "Pick at least one friend to invite.")

    def test_bad_value_is_rejected(self):
        self.client.force_login(self.organizer)
        self.client.post(self.url, {"friends": ["not-a-number"]})
        self.assertEqual(self.trip.memberships.count(), 2)

    def test_participant_gets_error_page_and_cannot_invite(self):
        self.client.force_login(self.participant)
        response = self.invite(self.stranger)
        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response, "Only the trip&#x27;s organizer can invite people.", status_code=403
        )
        self.assertNotIn(self.stranger.pk, self.member_ids())

    def test_participant_does_not_see_invite_form(self):
        self.client.force_login(self.participant)
        response = self.client.get(self.detail)
        self.assertNotContains(response, f'action="{self.url}"')
        self.assertNotIn("invitable", response.context)

    def test_non_member_gets_not_found(self):
        befriend(self.outsider, self.friend)
        self.client.force_login(self.outsider)
        self.assertEqual(self.invite(self.friend).status_code, 404)
        self.assertNotIn(self.friend.pk, self.member_ids())


class SeedInviteDemoTests(TestCase):
    def test_seeded_organizer_has_a_friend_to_invite(self):
        call_command("seed", stdout=StringIO())
        call_command("seed", stdout=StringIO())
        admin = User.objects.get(username="admin@example.com")
        trip = Trip.objects.get(organizer=admin)
        self.client.force_login(admin)
        response = self.client.get(reverse("trip_detail", args=[trip.pk]))
        names = [u.username for u in response.context["invitable"]]
        self.assertEqual(names, ["jordan.lee@example.com"])
