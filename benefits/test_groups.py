from django.test import SimpleTestCase, TestCase

from .engine import Outcome, RuleResult, evaluate_program, evaluate_rule
from .models import EligibilityRule, Jurisdiction, Program

TABLE = {
    "by": "family_type",
    "table": {"single_0": 60012, "couple_0": 64232},
}


class LookupTests(SimpleTestCase):
    def rule(self):
        return EligibilityRule(
            field="household_income", operator="lt_lookup", value=TABLE
        )

    def test_below_limit(self):
        facts = {"household_income": 50000, "family_type": "single_0"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.MET)

    def test_at_limit_is_not_met(self):
        facts = {"household_income": 60012, "family_type": "single_0"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.NOT_MET)

    def test_unknown_income(self):
        facts = {"household_income": None, "family_type": "single_0"}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.UNKNOWN)

    def test_unknown_household_type(self):
        facts = {"household_income": 50000}
        self.assertEqual(evaluate_rule(self.rule(), facts), RuleResult.UNKNOWN)

    def test_limit_depends_on_household_type(self):
        single = {"household_income": 62000, "family_type": "single_0"}
        couple = {"household_income": 62000, "family_type": "couple_0"}
        self.assertEqual(evaluate_rule(self.rule(), single), RuleResult.NOT_MET)
        self.assertEqual(evaluate_rule(self.rule(), couple), RuleResult.MET)


class GroupTests(TestCase):
    def setUp(self):
        federal = Jurisdiction.objects.create(
            code="CA", name="Canada (Federal)", level="federal"
        )
        self.program = Program.objects.create(
            jurisdiction=federal,
            name="Group program",
            category="benefit",
            source_url="https://example.com",
        )
        for description, field, operator, value in [
            ("19 or older", "age", "gte", 19),
            ("Has a partner", "has_partner", "eq", True),
        ]:
            EligibilityRule.objects.create(
                program=self.program,
                description=description,
                field=field,
                operator=operator,
                value=value,
                group="age_or_family",
            )
        EligibilityRule.objects.create(
            program=self.program,
            description="Tax resident",
            field="is_tax_resident",
            operator="eq",
            value=True,
        )

    def outcome(self, facts):
        return evaluate_program(self.program, facts).outcome

    def test_adult_passes(self):
        facts = {"age": 30, "has_partner": False, "is_tax_resident": True}
        self.assertEqual(self.outcome(facts), Outcome.MAY_QUALIFY)

    def test_minor_with_partner_passes(self):
        facts = {"age": 17, "has_partner": True, "is_tax_resident": True}
        self.assertEqual(self.outcome(facts), Outcome.MAY_QUALIFY)

    def test_minor_without_partner_fails(self):
        facts = {"age": 17, "has_partner": False, "is_tax_resident": True}
        self.assertEqual(self.outcome(facts), Outcome.DOES_NOT_QUALIFY)

    def test_unknown_residency_needs_info(self):
        facts = {"age": 30, "has_partner": False}
        self.assertEqual(self.outcome(facts), Outcome.NEEDS_INFO)