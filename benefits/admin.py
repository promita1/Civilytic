from django.contrib import admin

from .models import EligibilityRule, Jurisdiction, Program, RequiredDocument


class EligibilityRuleInline(admin.TabularInline):
    model = EligibilityRule
    extra = 0


class RequiredDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 0


@admin.register(Jurisdiction)
class JurisdictionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "level")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "jurisdiction", "category", "last_verified", "is_active")
    list_filter = ("jurisdiction", "category", "is_active")
    search_fields = ("name",)
    inlines = [EligibilityRuleInline, RequiredDocumentInline]