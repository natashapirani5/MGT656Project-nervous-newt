import re
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from abtest.models import ABVisitor
from abtest.views import AB_HASH, COOKIE_NAME, compute_stats

BUTTON_RE = re.compile(r'<button[^>]*id="abtest"[^>]*>(.*?)</button>', re.S)


class ABPageTests(TestCase):
    def setUp(self):
        self.page_url = f"/{AB_HASH}"
        self.click_url = f"/{AB_HASH}/click"

    def variant_from(self, response):
        buttons = BUTTON_RE.findall(response.content.decode())
        self.assertEqual(len(buttons), 1)
        return buttons[0].strip()

    def test_hash_is_correct(self):
        self.assertEqual(AB_HASH, "1ead64a")
        self.assertEqual(reverse("ab_page"), "/1ead64a")

    def test_public_200_without_login(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)

    def test_exactly_one_abtest_button_with_valid_text(self):
        html = self.client.get(self.page_url).content.decode()
        self.assertEqual(html.count('id="abtest"'), 1)
        self.assertIn(self.variant_from(self.client.get(self.page_url)), {"kudos", "thanks"})

    def test_page_lists_team_members(self):
        from abtest.views import TEAM_MEMBERS

        html = self.client.get(self.page_url).content.decode()
        for nickname in TEAM_MEMBERS:
            self.assertIn(nickname, html)

    def test_no_javascript_on_page(self):
        html = self.client.get(self.page_url).content.decode()
        self.assertNotIn("<script", html)

    def test_variant_is_sticky(self):
        first = self.variant_from(self.client.get(self.page_url))
        for _ in range(5):
            self.assertEqual(self.variant_from(self.client.get(self.page_url)), first)

    def test_one_impression_per_visitor_across_reloads(self):
        for _ in range(5):
            self.client.get(self.page_url)
        self.assertEqual(ABVisitor.objects.count(), 1)

    def test_at_most_one_click_per_visitor(self):
        self.client.get(self.page_url)
        first = self.client.post(self.click_url)
        clicked_at = ABVisitor.objects.get().clicked_at
        self.assertIsNotNone(clicked_at)
        self.client.post(self.click_url)
        self.client.post(self.click_url)
        self.assertEqual(ABVisitor.objects.get().clicked_at, clicked_at)
        self.assertEqual(first.status_code, 302)

    def test_click_redirect_does_not_add_impression_or_change_variant(self):
        variant = self.variant_from(self.client.get(self.page_url))
        response = self.client.post(self.click_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.variant_from(response), variant)
        self.assertEqual(ABVisitor.objects.count(), 1)

    def test_click_without_assigned_variant_is_not_counted(self):
        response = self.client.post(self.click_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ABVisitor.objects.count(), 0)

        client = Client()
        client.cookies[COOKIE_NAME] = "never-assigned"
        client.post(self.click_url)
        self.assertEqual(ABVisitor.objects.count(), 0)

    def test_click_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get(self.page_url)
        self.assertEqual(client.post(self.click_url).status_code, 403)

    def test_roughly_50_50_assignment(self):
        n = 400
        for _ in range(n):
            Client().get(self.page_url)
        kudos = ABVisitor.objects.filter(variant="kudos").count()
        self.assertEqual(ABVisitor.objects.count(), n)
        self.assertTrue(0.35 * n < kudos < 0.65 * n, kudos)

    def test_each_variant_is_rendered(self):
        for variant in ("kudos", "thanks"):
            with mock.patch("abtest.views.secrets.choice", return_value=variant):
                self.assertEqual(self.variant_from(Client().get(self.page_url)), variant)


class ABStatsTests(TestCase):
    def make(self, variant, impressions, clicks):
        for i in range(impressions):
            ABVisitor.objects.create(
                visitor_id=f"{variant}-{i}",
                variant=variant,
                clicked_at="2026-11-11T12:00:00Z" if i < clicks else None,
            )

    def test_zero_impressions(self):
        response = self.client.get(f"/{AB_HASH}/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["preferred"], "kudos")
        self.assertEqual(data["kudos"]["impressions"], 0)

    def test_math_uses_rate_not_raw_clicks(self):
        # thanks: 30/100 = 0.30 ; kudos: 40/200 = 0.20 -> thanks wins despite fewer clicks
        self.make("kudos", 200, 40)
        self.make("thanks", 100, 30)
        data = compute_stats()
        self.assertEqual(data["preferred"], "thanks")
        self.assertEqual(data["kudos"], {"impressions": 200, "clicks": 40, "click_rate": 0.2})
        self.assertEqual(data["thanks"]["clicks"], 30)

    def test_kudos_wins(self):
        self.make("kudos", 10, 5)
        self.make("thanks", 10, 1)
        self.assertEqual(self.client.get(f"/{AB_HASH}/stats").json()["preferred"], "kudos")

    def test_tie_is_deterministic(self):
        self.make("kudos", 10, 3)
        self.make("thanks", 20, 6)
        self.assertEqual(compute_stats()["preferred"], "kudos")

    def test_one_variant_without_impressions(self):
        self.make("thanks", 5, 1)
        self.assertEqual(compute_stats()["preferred"], "thanks")

    def test_stats_are_live(self):
        self.make("kudos", 1, 0)
        self.make("thanks", 1, 0)
        self.assertEqual(self.client.get(f"/{AB_HASH}/stats").json()["preferred"], "kudos")
        ABVisitor.objects.filter(variant="thanks").update(clicked_at="2026-11-11T12:00:00Z")
        self.assertEqual(self.client.get(f"/{AB_HASH}/stats").json()["preferred"], "thanks")


class ABResetCommandTests(TestCase):
    def test_reset_deletes_all_rows(self):
        ABVisitor.objects.create(visitor_id="a", variant="kudos")
        ABVisitor.objects.create(visitor_id="b", variant="thanks")
        call_command("abtest_reset", "--yes", stdout=StringIO())
        self.assertEqual(ABVisitor.objects.count(), 0)
