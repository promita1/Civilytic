from django.core.management.base import BaseCommand, CommandError

from benefits.engine import evaluate_person
from households.models import Household


class Command(BaseCommand):
    help = "Show program results for every person in a household"

    def add_arguments(self, parser):
        parser.add_argument("household_id", type=int)

    def handle(self, *args, **options):
        try:
            household = Household.objects.get(pk=options["household_id"])
        except Household.DoesNotExist:
            raise CommandError("No household with that id.")

        for person in household.members.all():
            self.stdout.write(f"\n{person}")
            for result in evaluate_person(person):
                self.stdout.write(f"  {result.program.name}: {result.outcome.value}")
                for rule, status in result.rule_results:
                    self.stdout.write(f"      [{status.value}] {rule.description}")