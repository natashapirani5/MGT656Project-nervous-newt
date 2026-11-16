from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from .models import Friendship, friends_of
from .templatetags.friend_tags import traveler_name

User = get_user_model()
MAX_RESULTS = 25


def _back_to_friends(request):
    q = request.POST.get("q", "").strip()
    url = reverse("friends")
    return redirect(f"{url}?{urlencode({'q': q})}" if q else url)


def _search(user, q):
    matches = (
        User.objects.filter(is_active=True)
        .filter(
            Q(profile__display_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__iexact=q)
            | Q(username__iexact=q)
        )
        .exclude(pk=user.pk)
        .select_related("profile")
        .order_by("profile__display_name", "first_name", "pk")[:MAX_RESULTS]
    )
    rows = {
        (f.from_user_id, f.to_user_id): f
        for f in Friendship.objects.filter(Q(from_user=user) | Q(to_user=user))
    }
    results = []
    for other in matches:
        sent = rows.get((user.pk, other.pk))
        received = rows.get((other.pk, user.pk))
        row = sent or received
        if row and row.status == Friendship.Status.ACCEPTED:
            state = "friends"
        elif sent:
            state = "sent"
        elif received:
            state = "received"
        else:
            state = "none"
        results.append({"user": other, "state": state})
    return results


@login_required
def friends_home(request):
    q = request.GET.get("q", "").strip()
    user = request.user
    context = {
        "q": q,
        "results": _search(user, q) if q else None,
        "incoming": Friendship.objects.filter(
            to_user=user, status=Friendship.Status.PENDING
        ).select_related("from_user__profile"),
        "outgoing": Friendship.objects.filter(
            from_user=user, status=Friendship.Status.PENDING
        ).select_related("to_user__profile"),
        "friends": friends_of(user).select_related("profile").order_by("profile__display_name"),
    }
    return render(request, "friends/index.html", context)


@login_required
@require_POST
def send_request(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)
    if other == request.user:
        return _back_to_friends(request)
    existing = Friendship.between(request.user, other)
    if existing is None:
        try:
            with transaction.atomic():
                Friendship.objects.create(from_user=request.user, to_user=other)
            messages.success(request, f"Friend request sent to {traveler_name(other)}.")
        except IntegrityError:
            pass  # a concurrent duplicate click; nothing to do
    elif existing.status == Friendship.Status.PENDING and existing.to_user == request.user:
        messages.info(
            request, f"{traveler_name(other)} already sent you a request. Accept it below."
        )
    # Already friends or already requested: do nothing.
    return _back_to_friends(request)


def _incoming_request(request, pk):
    # 404 for requests addressed to someone else, so they can't be accepted or probed.
    return get_object_or_404(
        Friendship, pk=pk, to_user=request.user, status=Friendship.Status.PENDING
    )


@login_required
@require_POST
def accept_request(request, pk):
    friend_request = _incoming_request(request, pk)
    friend_request.status = Friendship.Status.ACCEPTED
    friend_request.accepted_at = timezone.now()
    friend_request.save(update_fields=["status", "accepted_at"])
    messages.success(request, f"You and {traveler_name(friend_request.from_user)} are now friends.")
    return _back_to_friends(request)


@login_required
@require_POST
def decline_request(request, pk):
    friend_request = _incoming_request(request, pk)
    friend_request.delete()
    messages.info(request, "Request declined.")
    return _back_to_friends(request)


@login_required
@require_POST
def remove_friend(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    row = Friendship.between(request.user, other)
    if row and row.status == Friendship.Status.ACCEPTED:
        row.delete()
        messages.info(request, f"Removed {traveler_name(other)} from your friends.")
    return _back_to_friends(request)
