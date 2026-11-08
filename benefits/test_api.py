from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from households.models import Household, Person

from .models import EligibilityRule, Jurisdiction, Program


class ResultsApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user("owner", password="pw-for-tests-1")
        self.other = User.objects.create_user("other", password="pw-for-tests-2")
        federal = Jurisdiction.objects.create(
            code="CA", name="Canada (Federal)", level="federal"
        )
        alberta = Jurisdiction.objects.create(
            code="AB", name="Alberta", level="province"
        )
        program = Program.objects.create(
            jurisdiction=federal,
            name="Test program",
            category="benefit",
            source_url="https://example.com",
        )
        EligibilityRule.objects.create(
            program=program,
            description="Age 65 or older",
            field="age",
            operator="gte",
            value=65,
        )
        self.household = Household.objects.create(owner=self.owner, province=alberta)
        Person.objects.create(
            household=self.household,
            birth_date=date(1950, 1, 1),
            immigration_status="pr",
        )
        self.url = f"/api/households/{self.household.pk}/results/"

    def test_requires_login(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))

    def test_owner_gets_results(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        outcome = response.json()["people"][0]["programs"][0]["outcome"]
        self.assertEqual(outcome, "may_qualify")

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)