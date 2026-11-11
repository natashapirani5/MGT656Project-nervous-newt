from django.contrib import admin

from .models import ItineraryItem, Membership, Trip

admin.site.register(Trip)
admin.site.register(Membership)
admin.site.register(ItineraryItem)
