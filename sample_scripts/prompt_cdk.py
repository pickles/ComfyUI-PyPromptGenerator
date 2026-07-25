"""Small CDK-like framework for constrained random prompt generation."""

from dataclasses import dataclass
from itertools import product
from math import prod
from random import Random


@dataclass(frozen=True)
class Option:
    key: str
    prompt: str
    tags: frozenset[str]
    weight: float = 1.0
    negative: str = ""

    def has_tag(self, tag):
        return tag in self.tags


def option(key, prompt, *tags, weight=1.0, negative=""):
    """Create one selectable prompt fragment."""
    if weight <= 0:
        raise ValueError("Option weight must be greater than zero")
    return Option(key, prompt, frozenset(tags), float(weight), negative)


@dataclass(frozen=True)
class Condition:
    dimension: str
    key: str | None = None
    tag: str | None = None

    def matches(self, selection):
        selected = selection[self.dimension]
        if self.key is not None and selected.key != self.key:
            return False
        if self.tag is not None and not selected.has_tag(self.tag):
            return False
        return True

    def describe(self):
        criteria = []
        if self.key is not None:
            criteria.append(f"key={self.key}")
        if self.tag is not None:
            criteria.append(f"tag={self.tag}")
        return f"{self.dimension}({', '.join(criteria)})"


@dataclass(frozen=True)
class Rule:
    trigger: Condition
    target: Condition
    mode: str

    def accepts(self, selection):
        if not self.trigger.matches(selection):
            return True
        target_matches = self.target.matches(selection)
        return target_matches if self.mode == "require" else not target_matches

    def describe(self):
        verb = "requires" if self.mode == "require" else "forbids"
        return f"{self.trigger.describe()} {verb} {self.target.describe()}"


@dataclass(frozen=True)
class Scene:
    selection: dict[str, Option]

    def prompt(self, prefix="masterpiece, best quality, solo"):
        fragments = [prefix]
        fragments.extend(selected.prompt for selected in self.selection.values())
        return ", ".join(fragment for fragment in fragments if fragment)

    def summary(self):
        return {name: selected.key for name, selected in self.selection.items()}

    def negative_prompt(self, base=""):
        """Combine the base negative prompt with selected option negatives."""
        fragments = [base]
        fragments.extend(
            selected.negative
            for selected in self.selection.values()
            if selected.negative
        )
        return ", ".join(fragment for fragment in fragments if fragment)


class ConstraintBuilder:
    def __init__(self, program, trigger):
        self.program = program
        self.trigger = trigger

    def require(self, dimension, *, key=None, tag=None):
        self.program._add_rule(
            Rule(self.trigger, self.program._condition(dimension, key, tag), "require")
        )
        return self.program

    def forbid(self, dimension, *, key=None, tag=None):
        self.program._add_rule(
            Rule(self.trigger, self.program._condition(dimension, key, tag), "forbid")
        )
        return self.program


class PromptProgram:
    """Define prompt dimensions and synthesize a valid random scene."""

    def __init__(self, name):
        self.name = name
        self.dimensions = {}
        self.rules = []

    def dimension(self, name, *options):
        if name in self.dimensions:
            raise ValueError(f"Dimension already exists: {name}")
        if not options:
            raise ValueError(f"Dimension must contain at least one option: {name}")
        self.dimensions[name] = tuple(options)
        return self

    def when(self, dimension, *, key=None, tag=None):
        return ConstraintBuilder(self, self._condition(dimension, key, tag))

    def synth(self, seed=None):
        names = tuple(self.dimensions)
        candidates = []
        weights = []

        for values in product(*(self.dimensions[name] for name in names)):
            selection = dict(zip(names, values))
            if all(rule.accepts(selection) for rule in self.rules):
                candidates.append(selection)
                weights.append(prod(value.weight for value in values))

        if not candidates:
            rules = "\n".join(f"- {rule.describe()}" for rule in self.rules)
            raise ValueError(f"No valid prompt combinations for {self.name}:\n{rules}")

        selected = Random(seed).choices(candidates, weights=weights, k=1)[0]
        return Scene(selected)

    def _condition(self, dimension, key, tag):
        if dimension not in self.dimensions:
            raise KeyError(f"Unknown dimension: {dimension}")
        if key is None and tag is None:
            raise ValueError("A condition requires key or tag")
        return Condition(dimension, key, tag)

    def _add_rule(self, rule):
        self.rules.append(rule)
