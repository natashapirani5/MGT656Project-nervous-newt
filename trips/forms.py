import re

from django import forms

from friends.models import friends_of

from .models import ItineraryItem, Trip

WISHLIST_DATALIST_ID = "wishlist-destinations"


def wishlist_destinations(user):
    """The user's wishlist as a list, split on commas, semicolons, or new lines."""
    profile = getattr(user, "profile", None)
    raw = profile.wishlist_destinations if profile else ""
    seen = []
    for part in re.split(r"[,;\n]", raw):
        name = part.strip()
        if name and name.lower() not in (s.lower() for s in seen):
            seen.append(name)
    return seen


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ("destination", "start_date", "end_date", "description", "budget")
        labels = {
            "start_date": "Tentative start date",
            "end_date": "Tentative end date",
            "budget": "Budget (USD)",
        }
        widgets = {
            "destination": forms.TextInput(
                attrs={"class": "form-control", "list": WISHLIST_DATALIST_ID, "autocomplete": "off"}
            ),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "budget": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "1"}),
        }
        help_texts = {
            "destination": "Pick one from your wishlist or type any destination.",
        }

    def clean_destination(self):
        destination = self.cleaned_data["destination"].strip()
        if not destination:
            raise forms.ValidationError("Please enter a destination.")
        return destination

    def clean_budget(self):
        budget = self.cleaned_data.get("budget")
        if budget is not None and budget < 0:
            raise forms.ValidationError("Budget can't be negative.")
        return budget

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "The end date can't be before the start date.")
        return cleaned


class ItineraryItemForm(forms.ModelForm):
    """Add or edit one itinerary item. The date must fall within the trip's dates, if set."""

    class Meta:
        model = ItineraryItem
        fields = ("title", "date", "time", "location", "notes")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        help_texts = {"time": "Optional."}
        error_messages = {
            "title": {"required": "Please enter a title."},
            "date": {"required": "Please pick a date."},
        }

    def __init__(self, *args, trip, **kwargs):
        super().__init__(*args, **kwargs)
        self.trip = trip
        # Let the phone/desktop date picker grey out days outside the trip.
        if trip.start_date:
            self.fields["date"].widget.attrs["min"] = trip.start_date.isoformat()
        if trip.end_date:
            self.fields["date"].widget.attrs["max"] = trip.end_date.isoformat()

    def clean_date(self):
        date = self.cleaned_data["date"]
        start, end = self.trip.start_date, self.trip.end_date
        if (start and date < start) or (end and date > end):
            if start and end:
                window = f"between {start:%b} {start.day} and {end:%b} {end.day}, {end.year}"
            elif start:
                window = f"on or after {start:%b} {start.day}, {start.year}"
            else:
                window = f"on or before {end:%b} {end.day}, {end.year}"
            raise forms.ValidationError(f"Pick a date {window}, during the trip.")
        return date


class ProposeRemovalForm(forms.Form):
    reason = forms.CharField(
        label="Why remove it?",
        help_text="The organizer sees this when deciding.",
        max_length=300,
        error_messages={"required": "Please say why you'd remove it."},
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )


class InviteForm(forms.Form):
    """Pick friends to invite. Only the organizer's accepted friends are valid choices."""

    friends = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        error_messages={
            "required": "Pick at least one friend to invite.",
            "invalid_choice": "You can only invite your friends.",
            "invalid_pk_value": "You can only invite your friends.",
        },
    )

    def __init__(self, *args, organizer, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["friends"].queryset = friends_of(organizer)
