from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from households.models import Household

from .engine import evaluate_person
from .models import Program

DISCLAIMER = (
    "General information based on official sources. This is not legal, "
    "immigration or tax advice. Always confirm on the linked official page."
)


class ProgramSerializer(serializers.ModelSerializer):
    jurisdiction = serializers.CharField(source="jurisdiction.code")

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "jurisdiction",
            "category",
            "summary",
            "source_url",
            "last_verified",
        ]


class ProgramListView(ListAPIView):
    serializer_class = ProgramSerializer
    queryset = Program.objects.filter(is_active=True).select_related("jurisdiction")
    pagination_class = None


class HouseholdResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            household = Household.objects.select_related("province").get(
                pk=pk, owner=request.user
            )
        except Household.DoesNotExist:
            raise NotFound()

        people = []
        for person in household.members.all():
            programs = []
            for result in evaluate_person(person):
                programs.append(
                    {
                        "program": result.program.name,
                        "jurisdiction": result.program.jurisdiction.code,
                        "outcome": result.outcome.value,
                        "source_url": result.program.source_url,
                        "last_verified": result.program.last_verified,
                        "rules": [
                            {"description": rule.description, "status": status.value}
                            for rule, status in result.rule_results
                        ],
                    }
                )
            people.append({"person": str(person), "programs": programs})

        return Response(
            {"household": household.name, "people": people, "disclaimer": DISCLAIMER}
        )