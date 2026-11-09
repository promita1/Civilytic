from django.core.management.base import BaseCommand

from benefits.models import EligibilityRule, Jurisdiction, Program

OAS_URL = "https://www.canada.ca/en/services/benefits/publicpensions/old-age-security/eligibility.html"
CGEB_URL = "https://www.canada.ca/en/revenue-agency/services/child-family-benefits/canada-groceries-essentials-benefit/who-eligible.html"
ASB_URL = "https://www.alberta.ca/alberta-seniors-benefit"

# Maximum adjusted family net income limits, base year 2025.
# Copied from the official page; re-check them there each year.
CGEB_LIMITS = {
    "single_0": 60012,
    "single_1": 68912,
    "single_2": 73592,
    "single_3": 78272,
    "single_4": 82952,
    "couple_0": 64232,
    "couple_1": 68912,
    "couple_2": 73592,
    "couple_3": 78272,
    "couple_4": 82952,
}

# Guideline income levels effective July 1, 2026, for seniors whose income
# includes full OAS. Guidelines only. Re-check on the page each July.
ASB_LIMITS = {"single": 32690, "couple": 53800}

PROGRAMS = [
    {
        "jurisdiction": "CA",
        "name": "Old Age Security (OAS) pension",
        "category": "seniors",
        "summary": (
            "Monthly pension for people 65 or older who have lived in Canada "
            "long enough. Income can reduce or end payments (not checked yet)."
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
            {
                "description": "Lived in Canada at least 10 years since age 18",
                "field": "years_in_canada",
                "operator": "gte",
                "value": 10,
            },
        ],
    },
    {
        "jurisdiction": "CA",
        "name": "Canada Groceries and Essentials Benefit (CGEB)",
        "category": "benefit",
        "summary": (
            "Tax-free payments for people with low or modest income. Replaced "
            "the GST/HST credit in July 2026. Paid once per family, so both "
            "partners may show as eligible. Limits are for base year 2025."
        ),
        "source_url": CGEB_URL,
        "rules": [
            {
                "description": "Resident of Canada for income tax purposes",
                "field": "is_tax_resident",
                "operator": "eq",
                "value": True,
            },
            {
                "description": "Age 19 or older",
                "field": "age",
                "operator": "gte",
                "value": 19,
                "group": "age_or_family",
            },
            {
                "description": "Has a spouse or common-law partner (counts for people under 19)",
                "field": "has_partner",
                "operator": "eq",
                "value": True,
                "group": "age_or_family",
            },
            {
                "description": "Is a parent with a child in the household (counts for people under 19)",
                "field": "children_count",
                "operator": "gte",
                "value": 1,
                "group": "age_or_family",
            },
            {
                "description": (
                    "Family net income below the limit for your household type"
                ),
                "field": "household_income",
                "operator": "lt_lookup",
                "value": {"by": "family_type", "table": CGEB_LIMITS},
            },
        ],
    },
    {
        "jurisdiction": "AB",
        "name": "Alberta Seniors Benefit",
        "category": "seniors",
        "summary": (
            "Monthly help with living expenses for lower-income Alberta seniors. "
            "Income levels are guidelines only and deductions can change the "
            "result, so also use the official Seniors Benefit Estimator. The "
            "3-month Alberta residence condition, OAS deferral and benefit "
            "amounts are not checked yet. Paid per person or couple."
        ),
        "source_url": ASB_URL,
        "rules": [
            {
                "description": "Age 65 or older",
                "field": "age",
                "operator": "gte",
                "value": 65,
            },
            {
                "description": "Lives in Alberta",
                "field": "province",
                "operator": "eq",
                "value": "AB",
            },
            {
                "description": "Canadian citizen or permanent resident",
                "field": "immigration_status",
                "operator": "in",
                "value": ["citizen", "pr"],
            },
            {
                "description": "Receives the Old Age Security pension",
                "field": "receives_oas",
                "operator": "eq",
                "value": True,
            },
            {
                "description": (
                    "Income at or below the guideline for your household "
                    "(guideline only)"
                ),
                "field": "household_income",
                "operator": "lte_lookup",
                "value": {"by": "marital_group", "table": ASB_LIMITS},
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