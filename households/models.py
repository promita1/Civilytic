from django.conf import settings
from django.db import models


class Household(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="households"
    )
    name = models.CharField(max_length=100, default="My household")
    province = models.ForeignKey(
        "benefits.Jurisdiction",
        on_delete=models.PROTECT,
        limit_choices_to={"level__in": ["province", "territory"]},
    )
    annual_income_cad = models.PositiveIntegerField(
        null=True, blank=True, help_text="Approximate total household income"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Person(models.Model):
    class Status(models.TextChoices):
        CITIZEN = "citizen", "Canadian citizen"
        PR = "pr", "Permanent resident"
        STUDY_PERMIT = "study_permit", "Study permit holder"
        WORK_PERMIT = "work_permit", "Work permit holder"
        VISITOR = "visitor", "Visitor"
        REFUGEE_CLAIMANT = "refugee_claimant", "Refugee claimant"
        PROTECTED_PERSON = "protected_person", "Protected person"
        OTHER = "other", "Other"

    class Relationship(models.TextChoices):
        SELF = "self", "Self"
        PARTNER = "partner", "Spouse or partner"
        CHILD = "child", "Child"
        PARENT = "parent", "Parent"
        OTHER = "other", "Other"

    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="members"
    )
    relationship = models.CharField(
        max_length=10, choices=Relationship.choices, default=Relationship.SELF
    )
    birth_date = models.DateField()
    immigration_status = models.CharField(max_length=20, choices=Status.choices)
    is_student = models.BooleanField(default=False)
    has_disability = models.BooleanField(default=False)
    years_in_canada = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Years lived in Canada since age 18",
    )
    is_tax_resident = models.BooleanField(
        null=True,
        blank=True,
        help_text="Resident of Canada for income tax purposes (leave blank if unsure)",
    )
    receives_oas = models.BooleanField(
        null=True,
        blank=True,
        help_text="Receives the Old Age Security pension (leave blank if unsure)",
    )	

    def __str__(self):
        return f"{self.get_relationship_display()} ({self.get_immigration_status_display()})"