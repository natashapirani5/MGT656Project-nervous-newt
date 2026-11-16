from django import template

register = template.Library()


@register.filter
def traveler_name(user):
    """Public display name. Never falls back to username, since usernames are emails."""
    profile = getattr(user, "profile", None)
    return (profile and profile.display_name) or user.first_name or "Traveler"


@register.filter
def home_city(user):
    profile = getattr(user, "profile", None)
    return profile.home_city if profile else ""
