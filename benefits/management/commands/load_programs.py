from django.core.management.base import BaseCommand

from benefits.models import EligibilityRule, Jurisdiction, Program

OAS_URL = "https://www.canada.ca/en/services/benefits/publicpensions/old-age-security/eligibility.html"

PROGRAMS = [
    {
        "jurisdiction": "CA",
        "name": "Old Age Security (OAS) pension",
        "category": "seniors",
        "summary": (
            "Monthly pension for people 65 or older. Years of residence in "
            "Canada also matter and are not checked yet."
        ),
        "source_url": OAS_URL,
        "rules": [
            {
                "description": "Age 65 or older",
                "field": "age",
                "operator": "gte",
                "value": 65,
            },
            {
                "description": "Canadian citizen or legal resident (PR)",
                "field": "immigration_status",
                "operator": "in",
                "value": ["citizen", "pr"],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Load programs and their eligibility rules"

    def handle(self, *args, **options):
        for data in PROGRAMS:
            jurisdiction = Jurisdiction.objects.get(code=data["jurisdiction"])
            program, created = Program.objects.update_or_create(
                jurisdiction=jurisdiction,
                name=data["name"],
                defaults={
                    "category": data["category"],
                    "summary": data["summary"],
                    "source_url": data["source_url"],
                },
            )
            program.rules.all().delete()
            for rule in data["rules"]:
                EligibilityRule.objects.create(
                    program=program, source_url=data["source_url"], **rule
                )
            self.stdout.write(
                f"{'Created' if created else 'Updated'}: {program.name} "
                f"({len(data['rules'])} rules)"
            )