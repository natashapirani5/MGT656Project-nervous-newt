from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Trip


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
    trip = get_object_or_404(Trip, pk=pk)
    if not trip.is_member(request.user):
        # 404 rather than 403 so non-members can't probe which trips exist.
        raise Http404("Trip not found")
    days = {}
    for item in trip.itinerary_items.all():
        days.setdefault(item.date, []).append(item)
    context = {
        "trip": trip,
        "memberships": trip.memberships.select_related("user__profile"),
        "days": sorted(days.items()),
        "is_organizer": trip.is_organizer(request.user),
    }
    return render(request, "trips/detail.html", context)
