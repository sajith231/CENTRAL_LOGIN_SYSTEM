import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from activity_log.models import ActivityLog


class Command(BaseCommand):
    help = "Delete activity logs for a given month (default: the previous month)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            default=None,
            help="Month to clean, format YYYY-MM. Defaults to the previous month.",
        )

    def handle(self, *args, **options):
        raw = options.get("month")
        if raw:
            try:
                year, mon = (int(part) for part in raw.split("-"))
                datetime.date(year, mon, 1)
            except (ValueError, AttributeError):
                self.stderr.write(self.style.ERROR(f"Invalid month format: {raw} (expected YYYY-MM)"))
                return
        else:
            today = timezone.localtime().date()
            first_of_month = today.replace(day=1)
            prev = first_of_month - datetime.timedelta(days=1)
            year, mon = prev.year, prev.month

        queryset = ActivityLog.objects.filter(
            created_at__year=year, created_at__month=mon
        )
        deleted, _ = queryset.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} activity log record(s) for {mon:02d}-{year}."
            )
        )
