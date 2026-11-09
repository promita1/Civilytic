from households.models import Household, Person
from rest_framework.test import APITestCase

from .models import EligibilityRule, Jurisdiction, Program


class CheckEndpointTests(APITestCase):
    def setUp(self):
        federal = Jurisdiction.objects.create(
            code="CA", name="Canada (Federal)", level="federal"
        )
        Jurisdiction.objects.create(code="AB", name="Alberta", level="province")
        program = Program.objects.create(
            jurisdiction=federal,
            name="Test program",
            category="seniors",
            source_url="https://example.com",
        )
        EligibilityRule.objects.create(
            program=program,
            description="Age 65 or older",
            field="age",
            operator="gte",
            value=65,
        )
        self.url = "/api/check/"
        self.payload = {
            "province": "AB",
            "household_income": 30000,
            "members": [
                {
                    "relationship": "self",
                    "birth_date": "1950-01-01",
                    "immigration_status": "pr",
                }
            ],
        }

    def test_anonymous_request_returns_results(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 200)
        program = response.json()["people"][0]["programs"][0]
        self.assertEqual(program["outcome"], "may_qualify")

    def test_nothing_is_stored(self):
        self.client.post(self.url, self.payload, format="json")
        self.assertEqual(Household.objects.count(), 0)
        self.assertEqual(Person.objects.count(), 0)

    def test_unknown_province_is_rejected(self):
        self.payload["province"] = "XX"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_self_is_rejected(self):
        self.payload["members"][0]["relationship"] = "partner"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_future_birth_date_is_rejected(self):
        self.payload["members"][0]["birth_date"] = "2999-01-01"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 400)