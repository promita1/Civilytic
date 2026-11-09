from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class RuleResult(str, Enum):
    MET = "met"
    NOT_MET = "not_met"
    UNKNOWN = "unknown"


class Outcome(str, Enum):
    MAY_QUALIFY = "may_qualify"
    DOES_NOT_QUALIFY = "does_not_qualify"
    NEEDS_INFO = "needs_info"


OPERATORS = {
    "eq": lambda actual, expected: actual == expected,
    "neq": lambda actual, expected: actual != expected,
    "gt": lambda actual, expected: actual > expected,
    "gte": lambda actual, expected: actual >= expected,
    "lt": lambda actual, expected: actual < expected,
    "lte": lambda actual, expected: actual <= expected,
    "in": lambda actual, expected: actual in expected,
    "not_in": lambda actual, expected: actual not in expected,
}


@dataclass
class ProgramResult:
    program: object
    outcome: Outcome
    rule_results: list = field(default_factory=list)  # list of (rule, RuleResult)


def calculate_age(birth_date, today=None):
    today = today or date.today()
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


def build_facts(person, today=None):
    household = person.household
    members = list(household.members.all())

    # Partner and children are household facts. They apply to the adults who
    # would claim a family benefit, not to the children themselves.
    is_adult_claimant = person.relationship in ("self", "partner")
    has_partner = person.relationship == "partner" or (
        person.relationship == "self"
        and any(m.relationship == "partner" for m in members)
    )
    children_count = (
        sum(1 for m in members if m.relationship == "child")
        if is_adult_claimant
        else 0
    )

    return {
        "age": calculate_age(person.birth_date, today),
        "immigration_status": person.immigration_status,
        "relationship": person.relationship,
        "is_student": person.is_student,
        "has_disability": person.has_disability,
        "years_in_canada": person.years_in_canada,
        "is_tax_resident": person.is_tax_resident,
        "has_partner": has_partner,
        "children_count": children_count,
        "province": household.province.code,
        "household_income": household.annual_income_cad,
    }


def evaluate_rule(rule, facts):
    actual = facts.get(rule.field)
    if actual is None:
        return RuleResult.UNKNOWN
    compare = OPERATORS.get(rule.operator)
    if compare is None:
        return RuleResult.UNKNOWN
    try:
        return RuleResult.MET if compare(actual, rule.value) else RuleResult.NOT_MET
    except TypeError:
        return RuleResult.UNKNOWN


def evaluate_program(program, facts):
    rules = list(program.rules.all())
    results = [(rule, evaluate_rule(rule, facts)) for rule in rules]
    statuses = [status for _, status in results]

    if RuleResult.NOT_MET in statuses:
        outcome = Outcome.DOES_NOT_QUALIFY
    elif not rules or RuleResult.UNKNOWN in statuses:
        outcome = Outcome.NEEDS_INFO
    else:
        outcome = Outcome.MAY_QUALIFY
    return ProgramResult(program=program, outcome=outcome, rule_results=results)


def evaluate_person(person, programs=None, today=None):
    from .models import Program

    facts = build_facts(person, today)
    if programs is None:
        programs = (
            Program.objects.filter(
                is_active=True,
                jurisdiction__code__in=["CA", facts["province"]],
            )
            .select_related("jurisdiction")
            .prefetch_related("rules")
        )
    return [evaluate_program(program, facts) for program in programs]