from datetime import date

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from households.models import Household, Person

from .engine import RuleResult, evaluate_person, evaluate_rule
from .models import EligibilityRule, Jurisdiction, Program

TABLE = {"by": "marital_group", "table": {"single": 32690, "couple": 53800}}


class LteLookupTests(SimpleTestCase):
    def rule(self):
        return EligibilityRule(
            field="household_income", operator="lte_lookup", value=TABLE
        )

    def test_at_limit_is_met(self):
        facts = {"household_income": 32690, "marital_group": "single"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.MET)

    def test_above_limit_is_not_met(self):
        facts = {"household_income": 32691, "marital_group": "single"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.NOT_MET)

    def test_couple_limit_is_higher(self):
        couple = {"household_income": 40000, "marital_group": "couple"}
        single = {"household_income": 40000, "marital_group": "single"}
        self.assertEqual(evaluate_rule(self.rule(), couple), RuleResult.MET)
        self.assertEqual(evaluate_rule(self.rule(), single), RuleResult.NOT_MET)

    def test_unknown_income(self):
        facts = {"household_income": None, "marital_group": "single"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.UNKNOWN)


class ProvinceAwareTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "u", password="pw-for-tests-1"
        )
        federal = Jurisdiction.objects.create(
            code="CA", name="Canada (Federal)", level="federal"
        )
        self.alberta = Jurisdiction.objects.create(
            code="AB", name="Alberta", level="province"
        )
        self.ontario = Jurisdiction.objects.create(
            code="ON", name="Ontario", level="province"
        )
        for jurisdiction, name in [
            (federal, "Federal program"),
            (self.alberta, "Alberta program"),
            (self.ontario, "Ontario program"),
        ]:
            Program.objects.create(
                jurisdiction=jurisdiction,
                name=name,
                category="benefit",
                source_url="https://example.com",
            )

    def names_for(self, province):
        household = Household.objects.create(owner=self.user, province=province)
        person = Person.objects.create(
            household=household,
            birth_date=date(1950, 1, 1),
            immigration_status="pr",
        )
        return {r.program.name for r in evaluate_person(person)}

    def test_alberta_household(self):
        self.assertEqual(
            self.names_for(self.alberta), {"Federal program", "Alberta program"}
        )

    def test_ontario_household(self):
        self.assertEqual(
            self.names_for(self.ontario), {"Federal program", "Ontario program"}
        )