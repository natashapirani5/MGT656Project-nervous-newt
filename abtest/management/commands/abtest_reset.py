from django.core.management.base import BaseCommand

from abtest.models import ABVisitor


class Command(BaseCommand):
    help = "Delete ALL A/B test rows (impressions and clicks). Run before the bot run."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")

    def handle(self, *args, **options):
        count = ABVisitor.objects.count()
        if not options["yes"]:
            answer = input(f"Delete {count} A/B visitor rows? Type 'yes' to confirm: ")
            if answer.strip().lower() != "yes":
                self.stdout.write("Aborted.")
                return
        ABVisitor.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} A/B visitor rows."))
