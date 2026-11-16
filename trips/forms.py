import re

from django import forms

from .models import Trip

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
