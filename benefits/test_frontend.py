from django.test import TestCase


class FrontendTests(TestCase):
    def test_home_page_loads_with_notice(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not legal, immigration or tax advice")