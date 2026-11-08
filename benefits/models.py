from django.db import models


class Jurisdiction(models.Model):
    class Level(models.TextChoices):
        FEDERAL = "federal", "Federal"
        PROVINCE = "province", "Province"
        TERRITORY = "territory", "Territory"

    code = models.CharField(max_length=10, unique=True)  # e.g. CA, AB
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=Level.choices)

    class Meta:
        ordering = ["level", "name"]

    def __str__(self):
        return self.name


class Program(models.Model):
    class Category(models.TextChoices):
        BENEFIT = "benefit", "Benefit"
        TAX_CREDIT = "tax_credit", "Tax credit"
        IMMIGRATION = "immigration", "Immigration"
        SENIORS = "seniors", "Seniors"
        FAMILY = "family", "Family and children"
        STUDENT = "student", "Student"
        OTHER = "other", "Other"

    jurisdiction = models.ForeignKey(
        Jurisdiction, on_delete=models.PROTECT, related_name="programs"
    )
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices)
    summary = models.TextField(blank=True)
    source_url = models.URLField()
    last_verified = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["jurisdiction", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["jurisdiction", "name"], name="unique_program_per_jurisdiction"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.jurisdiction.code})"


class EligibilityRule(models.Model):
    class Operator(models.TextChoices):
        EQ = "eq", "equals"
        NEQ = "neq", "does not equal"
        GT = "gt", "greater than"
        GTE = "gte", "greater than or equal to"
        LT = "lt", "less than"
        LTE = "lte", "less than or equal to"
        IN = "in", "is one of"
        NOT_IN = "not_in", "is not one of"

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="rules")
    description = models.CharField(max_length=300)  # plain-language version
    field = models.CharField(max_length=100)  # e.g. "age", "immigration_status"
    operator = models.CharField(max_length=10, choices=Operator.choices)
    value = models.JSONField()  # e.g. 65, "pr", ["pr", "citizen"]
    source_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.program.name}: {self.field} {self.operator} {self.value}"


class RequiredDocument(models.Model):
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="required_documents"
    )
    name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.program.name}: {self.name}"