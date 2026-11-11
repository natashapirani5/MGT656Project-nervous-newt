"""A/B test page. Spec: CLAUDE.md, section "A/B test page" (follow exactly)."""

import secrets
import uuid

from django.db import IntegrityError
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .models import ABVisitor

AB_HASH = "1ead64a"  # first 7 chars of: printf %s ancient-water | shasum
COOKIE_NAME = "ab_visitor"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
VARIANTS = (ABVisitor.Variant.KUDOS, ABVisitor.Variant.THANKS)

TEAM_MEMBERS = ["crowded-dolphin", "cautious-crow", "lively-octopus", "busy-magpie"]


def _get_visitor(request):
    visitor_id = request.COOKIES.get(COOKIE_NAME)
    if not visitor_id:
        return None
    return ABVisitor.objects.filter(visitor_id=visitor_id).first()


def _assign_visitor(visitor_id):
    """Create the visitor (this is the one impression). Safe under concurrent requests."""
    try:
        return ABVisitor.objects.create(visitor_id=visitor_id, variant=secrets.choice(VARIANTS))
    except IntegrityError:
        return ABVisitor.objects.get(visitor_id=visitor_id)


@never_cache
@require_GET
def ab_page(request):
    visitor = _get_visitor(request)
    if visitor is None:
        visitor_id = request.COOKIES.get(COOKIE_NAME) or uuid.uuid4().hex
        visitor = _assign_visitor(visitor_id[:64])
    response = render(
        request,
        "abtest/page.html",
        {"variant": visitor.variant, "team_members": TEAM_MEMBERS, "ab_hash": AB_HASH},
    )
    response.set_cookie(
        COOKIE_NAME, visitor.visitor_id, max_age=COOKIE_MAX_AGE, httponly=True, samesite="Lax"
    )
    return response


@require_POST
def ab_click(request):
    visitor = _get_visitor(request)
    if visitor is not None:
        # Conditional update: only the first click per visitor is recorded.
        ABVisitor.objects.filter(pk=visitor.pk, clicked_at__isnull=True).update(
            clicked_at=timezone.now()
        )
    return redirect("ab_page")


def compute_stats():
    stats = {v.value: {"impressions": 0, "clicks": 0, "click_rate": 0.0} for v in VARIANTS}
    rows = ABVisitor.objects.values("variant").annotate(
        impressions=Count("id"), clicks=Count("clicked_at")
    )
    for row in rows:
        entry = stats[row["variant"]]
        entry["impressions"] = row["impressions"]
        entry["clicks"] = row["clicks"]
        entry["click_rate"] = row["clicks"] / row["impressions"] if row["impressions"] else 0.0
    # Tie-break (including zero impressions): "kudos".
    preferred = (
        "thanks" if stats["thanks"]["click_rate"] > stats["kudos"]["click_rate"] else "kudos"
    )
    return {"preferred": preferred, **stats}


@never_cache
@require_GET
def ab_stats(request):
    return JsonResponse(compute_stats())
