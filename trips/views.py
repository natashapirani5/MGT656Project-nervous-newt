from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from friends.models import friends_of
from friends.templatetags.friend_tags import traveler_name

from .forms import (
    WISHLIST_DATALIST_ID,
    InviteForm,
    ItineraryItemForm,
    TripForm,
    wishlist_destinations,
)
from .models import ItineraryItem, Membership, Trip


def _get_member_trip(request, pk):
    """Return the trip if the user is on it; 404 otherwise so non-members can't probe."""
    trip = get_object_or_404(Trip, pk=pk)
    if not trip.is_member(request.user):
        raise Http404("Trip not found")
    return trip


def _get_organizer_trip(request, pk, action):
    """Return the trip if the user organizes it; 404 for non-members, 403 for participants."""
    trip = _get_member_trip(request, pk)
    if not trip.is_organizer(request.user):
        raise PermissionDenied(f"Only the trip's organizer can {action}.")
    return trip


def _form_context(request, form, **extra):
    return {
        "form": form,
        "wishlist": wishlist_destinations(request.user),
        "datalist_id": WISHLIST_DATALIST_ID,
        **extra,
    }


@login_required
def dashboard(request):
    today = timezone.localdate()
    trips = (
        Trip.objects.filter(memberships__user=request.user)
        .exclude(end_date__lt=today)
        .select_related("organizer")
        .distinct()
    )
    return render(request, "trips/dashboard.html", {"trips": trips})


@login_required
def trip_detail(request, pk):
    trip = _get_member_trip(request, pk)
    days = {}
    for item in trip.itinerary_items.all():
        days.setdefault(item.date, []).append(item)
    is_organizer = trip.is_organizer(request.user)
    context = {
        "trip": trip,
        "memberships": trip.memberships.select_related("user__profile"),
        "days": sorted(days.items()),
        "is_organizer": is_organizer,
    }
    if is_organizer:
        context["invitable"] = (
            friends_of(request.user)
            .exclude(trip_memberships__trip=trip)
            .select_related("profile")
            .order_by("profile__display_name", "first_name", "pk")
        )
    return render(request, "trips/detail.html", context)


@login_required
def trip_create(request):
    form = TripForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            trip = form.save(commit=False)
            trip.organizer = request.user
            trip.save()
            Membership.objects.create(
                trip=trip,
                user=request.user,
                role=Membership.Role.ORGANIZER,
                rsvp=Membership.Rsvp.YES,
            )
        messages.success(request, f"Trip to {trip.destination} created. You're the organizer.")
        return redirect("trip_detail", pk=trip.pk)
    return render(
        request,
        "trips/form.html",
        _form_context(request, form, heading="Plan a new trip", submit_label="Create trip"),
    )


@login_required
def trip_edit(request, pk):
    trip = _get_member_trip(request, pk)
    if not trip.is_organizer(request.user):
        raise PermissionDenied("Only the trip's organizer can edit it.")
    form = TripForm(request.POST or None, instance=trip)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Trip details saved.")
        return redirect("trip_detail", pk=trip.pk)
    return render(
        request,
        "trips/form.html",
        _form_context(
            request,
            form,
            trip=trip,
            heading=f"Edit {trip.destination}",
            submit_label="Save changes",
        ),
    )


@login_required
def item_add(request, pk):
    trip = _get_organizer_trip(request, pk, "add itinerary items")
    form = ItineraryItemForm(request.POST or None, trip=trip)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.trip = trip
        # Items the organizer adds are approved straight away.
        item.status = ItineraryItem.Status.APPROVED
        item.proposed_by = request.user
        item.save()
        messages.success(request, f"Added “{item.title}” to the itinerary.")
        return redirect("trip_detail", pk=trip.pk)
    return render(
        request,
        "trips/item_form.html",
        {"form": form, "trip": trip, "heading": "Add an itinerary item", "submit_label": "Add"},
    )


@login_required
def item_edit(request, pk, item_pk):
    trip = _get_organizer_trip(request, pk, "edit itinerary items")
    item = get_object_or_404(ItineraryItem, pk=item_pk, trip=trip)
    form = ItineraryItemForm(request.POST or None, instance=item, trip=trip)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Saved “{item.title}”.")
        return redirect("trip_detail", pk=trip.pk)
    return render(
        request,
        "trips/item_form.html",
        {
            "form": form,
            "trip": trip,
            "heading": f"Edit “{item.title}”",
            "submit_label": "Save changes",
        },
    )


@login_required
def item_delete(request, pk, item_pk):
    """GET shows a confirmation page; POST deletes."""
    trip = _get_organizer_trip(request, pk, "remove itinerary items")
    item = get_object_or_404(ItineraryItem, pk=item_pk, trip=trip)
    if request.method == "POST":
        title = item.title
        item.delete()
        messages.success(request, f"Removed “{title}” from the itinerary.")
        return redirect("trip_detail", pk=trip.pk)
    return render(request, "trips/item_confirm_delete.html", {"trip": trip, "item": item})


@login_required
@require_POST
def trip_invite(request, pk):
    trip = _get_member_trip(request, pk)
    if not trip.is_organizer(request.user):
        raise PermissionDenied("Only the trip's organizer can invite people.")
    form = InviteForm(request.POST, organizer=request.user)
    if not form.is_valid():
        for error in form.errors.get("friends", []):
            messages.error(request, error)
        return redirect("trip_detail", pk=trip.pk)

    invited = []
    with transaction.atomic():
        for friend in form.cleaned_data["friends"]:
            _, created = Membership.objects.get_or_create(
                trip=trip,
                user=friend,
                defaults={
                    "role": Membership.Role.PARTICIPANT,
                    "rsvp": Membership.Rsvp.PENDING,
                },
            )
            if created:
                invited.append(traveler_name(friend))
    if invited:
        messages.success(request, f"Invited {', '.join(invited)}.")
    else:
        messages.info(request, "Everyone you picked is already on this trip.")
    return redirect("trip_detail", pk=trip.pk)
