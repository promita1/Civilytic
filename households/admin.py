from django.contrib import admin

from .models import Household, Person


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "province")
    inlines = [PersonInline]