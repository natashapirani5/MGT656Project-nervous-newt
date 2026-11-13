from django.contrib import admin

from .models import ABVisitor


@admin.register(ABVisitor)
class ABVisitorAdmin(admin.ModelAdmin):
    list_display = ("visitor_id", "variant", "impression_at", "clicked_at")
    list_filter = ("variant",)
