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

# Lookup operators compare against a limit chosen from a table by another fact.
LOOKUP_OPERATORS = {
    "lt_lookup": lambda actual, limit: actual < limit,
    "lte_lookup": lambda actual, limit: actual <= limit,
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


def build_facts(person, today=None, members=None):
    household = person.household
    if members is None:
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
        "receives_oas": person.receives_oas,
        "has_partner": has_partner,
        "children_count": children_count,
        "family_type": f"{'couple' if has_partner else 'single'}_{min(children_count, 4)}",
        "marital_group": "couple" if has_partner else "single",
        "province": household.province.code,
        "household_income": household.annual_income_cad,
    }


def evaluate_rule(rule, facts):
    actual = facts.get(rule.field)
    if actual is None:
        return RuleResult.UNKNOWN

    if rule.operator in LOOKUP_OPERATORS:
        if not isinstance(rule.value, dict):
            return RuleResult.UNKNOWN
        key = facts.get(rule.value.get("by"))
        limit = rule.value.get("table", {}).get(key)
        if limit is None:
            return RuleResult.UNKNOWN
        try:
            met = LOOKUP_OPERATORS[rule.operator](actual, limit)
        except TypeError:
            return RuleResult.UNKNOWN
        return RuleResult.MET if met else RuleResult.NOT_MET

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

    # Rules with the same non-empty group are alternatives: any one is enough.
    outcomes = []
    groups = {}
    for rule, status in results:
        if rule.group:
            groups.setdefault(rule.group, []).append(status)
        else:
            outcomes.append(status)
    for statuses in groups.values():
        if RuleResult.MET in statuses:
            outcomes.append(RuleResult.MET)
        elif all(s == RuleResult.NOT_MET for s in statuses):
            outcomes.append(RuleResult.NOT_MET)
        else:
            outcomes.append(RuleResult.UNKNOWN)

    if RuleResult.NOT_MET in outcomes:
        outcome = Outcome.DOES_NOT_QUALIFY
    elif not rules or RuleResult.UNKNOWN in outcomes:
        outcome = Outcome.NEEDS_INFO
    else:
        outcome = Outcome.MAY_QUALIFY
    return ProgramResult(program=program, outcome=outcome, rule_results=results)


def evaluate_person(person, programs=None, today=None, members=None):
    from .models import Program

    facts = build_facts(person, today, members)
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