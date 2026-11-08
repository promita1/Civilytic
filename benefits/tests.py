from datetime import date

from django.test import SimpleTestCase, TestCase

from .engine import Outcome, RuleResult, calculate_age, evaluate_program, evaluate_rule
from .models import EligibilityRule, Jurisdiction, Program


def make_rule(field, operator, value):
    return EligibilityRule(field=field, operator=operator, value=value)


class AgeTests(SimpleTestCase):
    def test_before_birthday(self):
        self.assertEqual(calculate_age(date(1960, 6, 15), date(2026, 6, 14)), 65)

    def test_on_birthday(self):
        self.assertEqual(calculate_age(date(1960, 6, 15), date(2026, 6, 15)), 66)


class RuleTests(SimpleTestCase):
    def test_met(self):
        self.assertEqual(
            evaluate_rule(make_rule("age", "gte", 65), {"age": 70}), RuleResult.MET
        )

    def test_not_met(self):
        self.assertEqual(
            evaluate_rule(make_rule("age", "gte", 65), {"age": 64}), RuleResult.NOT_MET
        )

    def test_missing_fact_is_unknown(self):
        self.assertEqual(
            evaluate_rule(make_rule("age", "gte", 65), {}), RuleResult.UNKNOWN
        )

    def test_none_fact_is_unknown(self):
        rule = make_rule("household_income", "lte", 50000)
        self.assertEqual(
            evaluate_rule(rule, {"household_income": None}), RuleResult.UNKNOWN
        )

    def test_in_operator(self):
        rule = make_rule("immigration_status", "in", ["pr", "citizen"])
        self.assertEqual(
            evaluate_rule(rule, {"immigration_status": "pr"}), RuleResult.MET
        )
        self.assertEqual(
            evaluate_rule(rule, {"immigration_status": "visitor"}), RuleResult.NOT_MET
        )


class ProgramTests(TestCase):
    def setUp(self):
        jurisdiction = Jurisdiction.objects.create(
            code="CA", name="Canada (Federal)", level="federal"
        )
        self.program = Program.objects.create(
            jurisdiction=jurisdiction,
            name="Test program",
            category="benefit",
            source_url="https://example.com",
        )
        EligibilityRule.objects.create(
            program=self.program, description="Age 65 or older",
            field="age", operator="gte", value=65,
        )
        EligibilityRule.objects.create(
            program=self.program, description="PR or citizen",
            field="immigration_status", operator="in", value=["pr", "citizen"],
        )

    def test_may_qualify(self):
        facts = {"age": 70, "immigration_status": "pr"}
        self.assertEqual(evaluate_program(self.program, facts).outcome, Outcome.MAY_QUALIFY)

    def test_does_not_qualify(self):
        facts = {"age": 40, "immigration_status": "pr"}
        self.assertEqual(evaluate_program(self.program, facts).outcome, Outcome.DOES_NOT_QUALIFY)

    def test_needs_info(self):
        facts = {"age": 70}
        self.assertEqual(evaluate_program(self.program, facts).outcome, Outcome.NEEDS_INFO)

    def test_failure_beats_missing_info(self):
        facts = {"age": 40}
        self.assertEqual(evaluate_program(self.program, facts).outcome, Outcome.DOES_NOT_QUALIFY)