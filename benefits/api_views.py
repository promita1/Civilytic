from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from households.models import Household, Person

from .engine import calculate_age, evaluate_person
from .models import Jurisdiction, Program

DISCLAIMER = (
    "General information based on official sources. This is not legal, "
    "immigration or tax advice. Always confirm on the linked official page."
)


def person_results(person, members=None):
    programs = []
    for result in evaluate_person(person, members=members):
        programs.append(
            {
                "program": result.program.name,
                "jurisdiction": result.program.jurisdiction.code,
                "outcome": result.outcome.value,
                "summary": result.program.summary,
                "source_url": result.program.source_url,
                "last_verified": result.program.last_verified,
                "rules": [
                    {
                        "description": rule.description,
                        "status": status.value,
                        "group": rule.group,
                    }
                    for rule, status in result.rule_results
                ],
            }
        )
    return {"person": str(person), "programs": programs}


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

        people = [person_results(person) for person in household.members.all()]
        return Response(
            {"household": household.name, "people": people, "disclaimer": DISCLAIMER}
        )


class MemberInputSerializer(serializers.Serializer):
    relationship = serializers.ChoiceField(choices=Person.Relationship.choices)
    birth_date = serializers.DateField()
    immigration_status = serializers.ChoiceField(choices=Person.Status.choices)
    years_in_canada = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=120
    )
    is_tax_resident = serializers.BooleanField(required=False, allow_null=True)
    receives_oas = serializers.BooleanField(required=False, allow_null=True)
    is_student = serializers.BooleanField(required=False)
    has_disability = serializers.BooleanField(required=False)

    def validate_birth_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Birth date cannot be in the future.")
        if calculate_age(value) > 120:
            raise serializers.ValidationError("Birth date is too far in the past.")
        return value


class CheckInputSerializer(serializers.Serializer):
    province = serializers.CharField()
    household_income = serializers.IntegerField(
        required=False, allow_null=True, min_value=0, max_value=10_000_000
    )
    members = MemberInputSerializer(many=True, allow_empty=False, max_length=12)

    def validate_province(self, value):
        try:
            return Jurisdiction.objects.get(
                code=value.upper(), level__in=["province", "territory"]
            )
        except Jurisdiction.DoesNotExist:
            raise serializers.ValidationError("Unknown province or territory code.")

    def validate_members(self, members):
        relationships = [m["relationship"] for m in members]
        if relationships.count("self") != 1:
            raise serializers.ValidationError(
                "Exactly one member must have relationship 'self'."
            )
        if relationships.count("partner") > 1:
            raise serializers.ValidationError("At most one spouse or partner.")
        return members


class CheckView(APIView):
    """Evaluate a household sent in the request. Nothing is stored."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = CheckInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        household = Household(
            province=data["province"],
            annual_income_cad=data.get("household_income"),
        )
        members = [
            Person(
                household=household,
                relationship=m["relationship"],
                birth_date=m["birth_date"],
                immigration_status=m["immigration_status"],
                is_student=m.get("is_student", False),
                has_disability=m.get("has_disability", False),
                years_in_canada=m.get("years_in_canada"),
                is_tax_resident=m.get("is_tax_resident"),
                receives_oas=m.get("receives_oas"),
            )
            for m in data["members"]
        ]

        people = [person_results(person, members=members) for person in members]
        return Response({"people": people, "disclaimer": DISCLAIMER})