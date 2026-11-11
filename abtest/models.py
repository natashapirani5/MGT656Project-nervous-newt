from django.db import models


class ABVisitor(models.Model):
    """One row per A/B visitor. The unique visitor_id guards against double counting."""

    class Variant(models.TextChoices):
        KUDOS = "kudos", "kudos"
        THANKS = "thanks", "thanks"

    visitor_id = models.CharField(max_length=64, unique=True)
    variant = models.CharField(max_length=10, choices=Variant.choices)
    impression_at = models.DateTimeField(auto_now_add=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ab_visitor"

    def __str__(self):
        return f"{self.visitor_id} {self.variant}"
