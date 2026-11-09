from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from benefits.models import Jurisdiction
from households.models import Household, Person

DEMO_USERNAME = "demo"

DEMO_HOUSEHOLDS = [
    {
        "name": "Demo: retired permanent resident",
        "province": "AB",
        "income": 32000,
        "members": [
            {
                "relationship": "self",
                "birth_date": date(1955, 3, 15),
                "status": "pr",
                "years": 20,
            },
        ],
    },
    {
        "name": "Demo: family with a young child",
        "province": "AB",
        "income": 78000,
        "members": [
            {
                "relationship": "self",
                "birth_date": date(1988, 7, 2),
                "status": "pr",
                "years": 8,
            },
            {
                "relationship": "partner",
                "birth_date": date(1990, 1, 20),
                "status": "work_permit",
                "years": 3,
            },
            {
                "relationship": "child",
                "birth_date": date(2018, 6, 1),
                "status": "citizen",
                "years": None,
            },
        ],
    },
    {
        "name": "Demo: international student",
        "province": "AB",
        "income": 18000,
        "members": [
            {
                "relationship": "self",
                "birth_date": date(1999, 11, 5),
                "status": "study_permit",
                "years": 2,
                "student": True,
            },
        ],
    },
    {
        "name": "Demo: recent newcomer on a work permit",
        "province": "AB",
        "income": None,
        "members": [
            {
                "relationship": "self",
                "birth_date": date(1985, 4, 9),
                "status": "work_permit",
                "years": None,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Create a demo user and fictional demo households (safe to re-run)"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=DEMO_USERNAME)
        if created:
            user.set_unusable_password()
            user.save()

        user.households.all().delete()

        for data in DEMO_HOUSEHOLDS:
            try:
                province = Jurisdiction.objects.get(code=data["province"])
            except Jurisdiction.DoesNotExist:
                raise CommandError("Run load_jurisdictions first.")

            household = Household.objects.create(
                owner=user,
                name=data["name"],
                province=province,
                annual_income_cad=data["income"],
            )
            for member in data["members"]:
                Person.objects.create(
                    household=household,
                    relationship=member["relationship"],
                    birth_date=member["birth_date"],
                    immigration_status=member["status"],
                    is_student=member.get("student", False),
                    years_in_canada=member["years"],
                )
            self.stdout.write(f"Household {household.pk}: {household.name}")