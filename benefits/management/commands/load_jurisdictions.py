from django.core.management.base import BaseCommand

from benefits.models import Jurisdiction

JURISDICTIONS = [
    ("CA", "Canada (Federal)", "federal"),
    ("AB", "Alberta", "province"),
    ("BC", "British Columbia", "province"),
    ("MB", "Manitoba", "province"),
    ("NB", "New Brunswick", "province"),
    ("NL", "Newfoundland and Labrador", "province"),
    ("NS", "Nova Scotia", "province"),
    ("ON", "Ontario", "province"),
    ("PE", "Prince Edward Island", "province"),
    ("QC", "Quebec", "province"),
    ("SK", "Saskatchewan", "province"),
    ("NT", "Northwest Territories", "territory"),
    ("NU", "Nunavut", "territory"),
    ("YT", "Yukon", "territory"),
]


class Command(BaseCommand):
    help = "Load federal, provincial and territorial jurisdictions"

    def handle(self, *args, **options):
        for code, name, level in JURISDICTIONS:
            obj, created = Jurisdiction.objects.update_or_create(
                code=code, defaults={"name": name, "level": level}
            )
            self.stdout.write(f"{'Created' if created else 'Updated'}: {obj.name}")