import re
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from friends.models import Friendship, are_friends, friends_of


def make_user(email, name, city=""):
    user = User.objects.create_user(email, email=email, password="pw-strong-123", first_name=name)
    Profile.objects.create(user=user, display_name=name, home_city=city)
    return user


class FriendsTestCase(TestCase):
    def setUp(self):
        self.alice = make_user("alice@example.com", "Alice Adams", "New Haven, CT")
        self.bob = make_user("bob@example.com", "Bob Brown", "Boston, MA")
        self.carol = make_user("carol@example.com", "Carol Chen")
        self.url = reverse("friends")

    def request_friend(self, sender, recipient):
        self.client.force_login(sender)
        return self.client.post(reverse("friend_request_send", args=[recipient.pk]))


class SearchTests(FriendsTestCase):
    """#23: search for users."""

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_friends_link_in_menu(self):
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(reverse("dashboard")), f'href="{self.url}"')

    def test_search_by_name(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url, {"q": "bob"})
        self.assertContains(response, "Bob Brown")
        self.assertContains(response, "Boston, MA")
        self.assertNotContains(response, "Carol Chen")

    def test_search_by_email(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url, {"q": "carol@example.com"})
        self.assertContains(response, "Carol Chen")

    def test_results_never_show_email(self):
        self.client.force_login(self.alice)
        for q in ("bob", "bob@example.com"):
            response = self.client.get(self.url, {"q": q})
            self.assertContains(response, "Bob Brown")
            # The search form echoes what the user typed in input values; the visible page
            # text must never contain anyone's email.
            visible_text = re.sub(r"<[^>]+>", " ", response.content.decode())
            self.assertNotIn("bob@example.com", visible_text)
            self.assertNotIn("alice@example.com", response.content.decode())
        self.assertNotContains(self.client.get(self.url, {"q": "bob"}), "bob@example.com")

    def test_user_not_in_own_results(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url, {"q": "alice"})
        self.assertEqual(response.context["results"], [])
        self.assertContains(response, "No travelers found")

    def test_no_matches(self):
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(self.url, {"q": "zzz"}), "No travelers found")

    def test_no_search_shows_no_results_section(self):
        self.client.force_login(self.alice)
        response = self.client.get(self.url)
        self.assertIsNone(response.context["results"])
        self.assertNotContains(response, "No travelers found")

    def test_partial_email_does_not_match(self):
        # Partial emails would let people enumerate addresses; only exact emails match.
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(self.url, {"q": "@example.com"}), "No travelers found")

    def test_result_shows_relationship_state(self):
        self.request_friend(self.alice, self.bob)
        response = self.client.get(self.url, {"q": "bob"})
        self.assertContains(response, "Request sent")
        self.assertNotContains(response, "Add friend")


class FriendRequestTests(FriendsTestCase):
    """#24: send, accept, and decline friend requests."""

    def test_send_request(self):
        response = self.request_friend(self.alice, self.bob)
        self.assertRedirects(response, self.url)
        row = Friendship.objects.get()
        self.assertEqual(
            (row.from_user, row.to_user, row.status), (self.alice, self.bob, "pending")
        )

    def test_send_request_keeps_search(self):
        self.client.force_login(self.alice)
        response = self.client.post(
            reverse("friend_request_send", args=[self.bob.pk]), {"q": "bob"}
        )
        self.assertRedirects(response, f"{self.url}?q=bob")

    def test_send_requires_login_and_post(self):
        url = reverse("friend_request_send", args=[self.bob.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Friendship.objects.count(), 0)

    def test_second_request_does_nothing(self):
        self.request_friend(self.alice, self.bob)
        self.request_friend(self.alice, self.bob)
        self.assertEqual(Friendship.objects.count(), 1)

    def test_request_to_existing_friend_does_nothing(self):
        Friendship.objects.create(from_user=self.alice, to_user=self.bob, status="accepted")
        self.request_friend(self.alice, self.bob)
        self.request_friend(self.bob, self.alice)
        self.assertEqual(Friendship.objects.count(), 1)
        self.assertEqual(Friendship.objects.get().status, "accepted")

    def test_reverse_request_does_not_duplicate(self):
        self.request_friend(self.alice, self.bob)
        response = self.request_friend(self.bob, self.alice)
        self.assertEqual(Friendship.objects.count(), 1)
        self.assertContains(self.client.get(response.url), "already sent you a request")

    def test_cannot_request_self(self):
        self.request_friend(self.alice, self.alice)
        self.assertEqual(Friendship.objects.count(), 0)

    def test_database_blocks_self_and_duplicate_rows(self):
        Friendship.objects.create(from_user=self.alice, to_user=self.bob)
        for kwargs in (
            {"from_user": self.alice, "to_user": self.alice},
            {"from_user": self.alice, "to_user": self.bob},
        ):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Friendship.objects.create(**kwargs)

    def test_recipient_sees_pending_request(self):
        self.request_friend(self.alice, self.bob)
        self.client.force_login(self.bob)
        response = self.client.get(self.url)
        self.assertContains(response, "Alice Adams")
        self.assertContains(response, "Accept")
        self.assertContains(response, "Decline")
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(self.url), "Waiting for a reply")

    def test_accept_makes_both_friends(self):
        self.request_friend(self.alice, self.bob)
        row = Friendship.objects.get()
        self.client.force_login(self.bob)
        response = self.client.post(reverse("friend_request_accept", args=[row.pk]))
        self.assertRedirects(response, self.url)
        self.assertTrue(are_friends(self.alice, self.bob))
        self.assertTrue(are_friends(self.bob, self.alice))
        self.assertEqual(list(friends_of(self.alice)), [self.bob])
        self.assertEqual(list(friends_of(self.bob)), [self.alice])

    def test_decline_removes_request(self):
        self.request_friend(self.alice, self.bob)
        row = Friendship.objects.get()
        self.client.force_login(self.bob)
        self.client.post(reverse("friend_request_decline", args=[row.pk]))
        self.assertEqual(Friendship.objects.count(), 0)
        self.assertFalse(are_friends(self.alice, self.bob))

    def test_only_recipient_can_accept_or_decline(self):
        self.request_friend(self.alice, self.bob)
        row = Friendship.objects.get()
        for intruder in (self.alice, self.carol):
            self.client.force_login(intruder)
            for name in ("friend_request_accept", "friend_request_decline"):
                response = self.client.post(reverse(name, args=[row.pk]))
                self.assertEqual(response.status_code, 404)
        row.refresh_from_db()
        self.assertEqual(row.status, "pending")

    def test_cannot_accept_already_accepted_request_again(self):
        row = Friendship.objects.create(from_user=self.alice, to_user=self.bob, status="accepted")
        self.client.force_login(self.bob)
        response = self.client.post(reverse("friend_request_decline", args=[row.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(are_friends(self.alice, self.bob))


class FriendsListTests(FriendsTestCase):
    """#25: my friends list."""

    def setUp(self):
        super().setUp()
        Friendship.objects.create(from_user=self.alice, to_user=self.bob, status="accepted")

    def test_lists_friends_for_both_people(self):
        self.client.force_login(self.alice)
        self.assertEqual(list(self.client.get(self.url).context["friends"]), [self.bob])
        self.client.force_login(self.bob)
        self.assertEqual(list(self.client.get(self.url).context["friends"]), [self.alice])

    def test_pending_requests_are_not_friends(self):
        Friendship.objects.create(from_user=self.carol, to_user=self.alice)
        self.client.force_login(self.alice)
        self.assertNotIn(self.carol, self.client.get(self.url).context["friends"])

    def test_remove_friend_removes_for_both(self):
        self.client.force_login(self.bob)
        response = self.client.post(reverse("friend_remove", args=[self.alice.pk]))
        self.assertRedirects(response, self.url)
        self.assertFalse(are_friends(self.alice, self.bob))
        self.assertEqual(list(friends_of(self.alice)), [])

    def test_remove_does_not_touch_other_peoples_friendships(self):
        self.client.force_login(self.carol)
        self.client.post(reverse("friend_remove", args=[self.alice.pk]))
        self.assertTrue(are_friends(self.alice, self.bob))

    def test_remove_does_not_cancel_pending_request(self):
        Friendship.objects.create(from_user=self.carol, to_user=self.alice)
        self.client.force_login(self.alice)
        self.client.post(reverse("friend_remove", args=[self.carol.pk]))
        self.assertEqual(Friendship.objects.filter(from_user=self.carol).count(), 1)


class SeedFriendsTests(TestCase):
    def test_seed_makes_graders_friends_and_is_idempotent(self):
        call_command("seed", stdout=StringIO())
        call_command("seed", stdout=StringIO())
        admin = User.objects.get(username="admin@example.com")
        member = User.objects.get(username="member@example.com")
        self.assertTrue(are_friends(admin, member))
        self.assertEqual(Friendship.objects.count(), 3)
        self.assertEqual(Friendship.objects.filter(to_user=admin, status="pending").count(), 1)
        self.assertEqual(Friendship.objects.filter(to_user=member, status="pending").count(), 1)

    def test_reseed_keeps_accepted_demo_requests(self):
        call_command("seed", stdout=StringIO())
        admin = User.objects.get(username="admin@example.com")
        Friendship.objects.filter(to_user=admin, status="pending").update(status="accepted")
        call_command("seed", stdout=StringIO())
        self.assertEqual(friends_of(admin).count(), 2)

    def test_demo_travelers_cannot_log_in(self):
        call_command("seed", stdout=StringIO())
        self.assertFalse(User.objects.get(username="sam.rivera@example.com").has_usable_password())
