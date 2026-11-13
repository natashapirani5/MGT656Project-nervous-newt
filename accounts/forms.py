from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class SignUpForm(UserCreationForm):
    """Sign up with an email address; the email doubles as the username."""

    email = forms.EmailField()
    display_name = forms.CharField(max_length=100, label="Name")

    class Meta:
        model = User
        fields = ("email", "display_name")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["display_name"]
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user, defaults={"display_name": self.cleaned_data["display_name"]}
            )
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "home_city",
            "interests",
            "wishlist_destinations",
            "trip_preferences",
        )
        widgets = {
            "interests": forms.Textarea(attrs={"rows": 2}),
            "wishlist_destinations": forms.Textarea(attrs={"rows": 2}),
            "trip_preferences": forms.Textarea(attrs={"rows": 2}),
        }
