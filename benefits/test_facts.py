from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from households.models import Household, Person

from .engine import build_facts
from .models import Jurisdiction


class HouseholdFactsTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("u", password="pw-for-tests-1")
        alberta = Jurisdiction.objects.create(
            code="AB", name="Alberta", level="province"
        )
        self.household = Household.objects.create(
            owner=user, province=alberta, annual_income_cad=50000
        )

    def add(self, relationship, year):
        return Person.objects.create(
            household=self.household,
            relationship=relationship,
            birth_date=date(year, 1, 1),
            immigration_status="pr",
        )

    def test_family_facts(self):
        me = self.add("self", 1988)
        partner = self.add("partner", 1990)
        self.add("child", 2018)
        kid = self.add("child", 2020)

        self.assertTrue(build_facts(me)["has_partner"])
        self.assertEqual(build_facts(me)["children_count"], 2)
        self.assertTrue(build_facts(partner)["has_partner"])
        self.assertEqual(build_facts(partner)["children_count"], 2)
        self.assertFalse(build_facts(kid)["has_partner"])
        self.assertEqual(build_facts(kid)["children_count"], 0)

    def test_single_person(self):
        me = self.add("self", 1988)
        facts = build_facts(me)
        self.assertFalse(facts["has_partner"])
        self.assertEqual(facts["children_count"], 0)

    def test_tax_residency_unknown_by_default(self):
        me = self.add("self", 1988)
        self.assertIsNone(build_facts(me)["is_tax_resident"])