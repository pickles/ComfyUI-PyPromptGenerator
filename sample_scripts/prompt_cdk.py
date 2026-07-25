"""Small CDK-like framework for constrained random prompt generation."""

from dataclasses import dataclass
from itertools import product
from math import prod
from random import Random


@dataclass(frozen=True)
class Option:
    key: str
    prompt: str | tuple[str, ...]
    tags: frozenset[str]
    weight: float = 1.0
    negative: str = ""
    break_before: bool = False

    def has_tag(self, tag):
        return tag in self.tags


def option(key, prompt, *tags, weight=1.0, negative="", break_before=False):
    """Create one selectable prompt fragment or group of fragments."""
    if weight <= 0:
        raise ValueError("Option weight must be greater than zero")
    prompt = _normalize_fragments(prompt, "option")
    return Option(
        key,
        prompt,
        frozenset(tags),
        float(weight),
        negative,
        bool(break_before),
    )


@dataclass(frozen=True)
class Condition:
    dimension: str
    keys: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    match: str = "all"

    def matches(self, selection):
        selected = selection[self.dimension]
        if self.keys and selected.key not in self.keys:
            return False
        if self.tags:
            tag_matches = [selected.has_tag(tag) for tag in self.tags]
            if self.match == "all" and not all(tag_matches):
                return False
            if self.match == "any" and not any(tag_matches):
                return False
        return True

    def describe(self):
        criteria = []
        if self.keys:
            criteria.append(f"keys(any)={sorted(self.keys)}")
        if self.tags:
            criteria.append(f"tags({self.match})={sorted(self.tags)}")
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
    elements: tuple[tuple[str, str | None], ...]

    def prompt(self, prefix="masterpiece, best quality, solo"):
        lines = []
        if prefix:
            lines.append(prefix)

        for element_type, value in self.elements:
            if element_type == "break":
                lines.append("BREAK")
            elif element_type == "fixed":
                lines.append(value)
            elif element_type == "dimension":
                selected = self.selection[value]
                if selected.break_before and lines and lines[-1] != "BREAK":
                    lines.append("BREAK")
                if selected.prompt:
                    if isinstance(selected.prompt, str):
                        lines.append(selected.prompt)
                    else:
                        lines.extend(selected.prompt)

        return self._render_lines(lines)

    def summary(self):
        return {name: selected.key for name, selected in self.selection.items()}

    def negative_prompt(self, base=""):
        """Combine the base negative prompt with selected option negatives."""
        lines = [base]
        lines.extend(
            selected.negative
            for selected in self.selection.values()
            if selected.negative
        )
        return self._render_lines([line for line in lines if line])

    @staticmethod
    def _render_lines(lines):
        """Render prompt fragments one per line, preserving standalone BREAK."""
        last_text_index = max(
            (index for index, line in enumerate(lines) if line != "BREAK"),
            default=-1,
        )
        rendered = []
        for index, line in enumerate(lines):
            if line == "BREAK":
                rendered.append(line)
            elif index == last_text_index:
                rendered.append(line)
            else:
                rendered.append(f"{line},")
        return "\n".join(rendered)


class ConstraintBuilder:
    def __init__(self, program, trigger, resolve_dimension=None, return_target=None):
        self.program = program
        self.trigger = trigger
        self.resolve_dimension = resolve_dimension or (lambda dimension: dimension)
        self.return_target = return_target or program

    def require(
        self,
        dimension,
        *,
        key=None,
        keys=None,
        tag=None,
        tags=None,
        match="all",
    ):
        dimension = self.resolve_dimension(dimension)
        self.program._add_rule(
            Rule(
                self.trigger,
                self.program._condition(
                    dimension,
                    key,
                    keys,
                    tag,
                    tags,
                    match,
                ),
                "require",
            )
        )
        return self.return_target

    def forbid(
        self,
        dimension,
        *,
        key=None,
        keys=None,
        tag=None,
        tags=None,
        match="all",
    ):
        dimension = self.resolve_dimension(dimension)
        self.program._add_rule(
            Rule(
                self.trigger,
                self.program._condition(
                    dimension,
                    key,
                    keys,
                    tag,
                    tags,
                    match,
                ),
                "forbid",
            )
        )
        return self.return_target


class PromptBlock:
    """Group fixed fragments and dimensions so related tokens stay together."""

    def __init__(self, program, name):
        self.program = program
        self.name = name

    def fixed(self, value):
        self.program._add_fixed(value)
        return self

    def dimension(self, name, *options, break_before=False):
        self.program._add_dimension(
            self._scope(name),
            options,
            break_before=break_before,
        )
        return self

    def break_(self):
        self.program._add_break()
        return self

    def when(
        self,
        dimension,
        *,
        key=None,
        keys=None,
        tag=None,
        tags=None,
        match="all",
    ):
        trigger = self.program._condition(
            self._scope(dimension),
            key,
            keys,
            tag,
            tags,
            match,
        )
        return ConstraintBuilder(
            self.program,
            trigger,
            resolve_dimension=self._scope,
            return_target=self,
        )

    def _scope(self, dimension):
        if "." in dimension:
            return dimension
        return f"{self.name}.{dimension}"


class PromptProgram:
    """Define prompt dimensions and synthesize a valid random scene."""

    def __init__(self, name):
        self.name = name
        self.dimensions = {}
        self.elements = []
        self.block_names = set()
        self.rules = []

    def dimension(self, name, *options, break_before=False):
        self._add_dimension(name, options, break_before=break_before)
        return self

    def fixed(self, value):
        """Add one fixed string or a list of fixed strings."""
        self._add_fixed(value)
        return self

    def block(self, name, value=None, *, break_before=False):
        """Create a named block whose dimensions use scoped names."""
        if name in self.block_names:
            raise ValueError(f"Block already exists: {name}")
        self.block_names.add(name)
        if break_before:
            self._add_break()
        block = PromptBlock(self, name)
        if value is not None:
            block.fixed(value)
        return block

    def break_(self):
        """Insert BREAK at the current position in the prompt."""
        self._add_break()
        return self

    def when(
        self,
        dimension,
        *,
        key=None,
        keys=None,
        tag=None,
        tags=None,
        match="all",
    ):
        return ConstraintBuilder(
            self,
            self._condition(dimension, key, keys, tag, tags, match),
        )

    def synth(self, seed=None):
        if self.elements and self.elements[-1][0] == "break":
            raise ValueError("break_() must be followed by prompt content")

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
        return Scene(selected, tuple(self.elements))

    def _add_dimension(self, name, options, *, break_before=False):
        if name in self.dimensions:
            raise ValueError(f"Dimension already exists: {name}")
        if not options:
            raise ValueError(f"Dimension must contain at least one option: {name}")
        if break_before:
            self._add_break()
        self.dimensions[name] = tuple(options)
        self.elements.append(("dimension", name))

    def _add_fixed(self, value):
        normalized = _normalize_fragments(value, "fixed")
        fragments = [normalized] if isinstance(normalized, str) else normalized
        for fragment in fragments:
            if fragment:
                self.elements.append(("fixed", fragment))

    def _add_break(self):
        self.elements.append(("break", None))

    def _condition(self, dimension, key, keys, tag, tags, match):
        if dimension not in self.dimensions:
            raise KeyError(f"Unknown dimension: {dimension}")
        if key is not None and keys is not None:
            raise ValueError("Use either key or keys, not both")
        if tag is not None and tags is not None:
            raise ValueError("Use either tag or tags, not both")
        if match not in {"all", "any"}:
            raise ValueError("match must be 'all' or 'any'")

        if key is not None:
            normalized_keys = frozenset([key])
        elif keys is None:
            normalized_keys = frozenset()
        else:
            if isinstance(keys, str):
                raise TypeError("keys must be a list of strings")
            try:
                normalized_keys = frozenset(keys)
            except TypeError as error:
                raise TypeError("keys must be a list of strings") from error

        if any(not isinstance(item, str) for item in normalized_keys):
            raise TypeError("keys must be a list of strings")

        if tag is not None:
            normalized_tags = frozenset([tag])
        elif tags is None:
            normalized_tags = frozenset()
        else:
            if isinstance(tags, str):
                raise TypeError("tags must be a list of strings")
            try:
                normalized_tags = frozenset(tags)
            except TypeError as error:
                raise TypeError("tags must be a list of strings") from error

        if any(not isinstance(item, str) for item in normalized_tags):
            raise TypeError("tags must be a list of strings")
        if not normalized_keys and not normalized_tags:
            raise ValueError("A condition requires key, keys, tag, or tags")
        return Condition(dimension, normalized_keys, normalized_tags, match)

    def _add_rule(self, rule):
        self.rules.append(rule)


def _normalize_fragments(value, function_name):
    error_message = (
        f"{function_name}() accepts a string or a list of strings"
    )
    if isinstance(value, str):
        return value
    if not isinstance(value, (list, tuple)):
        raise TypeError(error_message)
    if any(not isinstance(fragment, str) for fragment in value):
        raise TypeError(error_message)
    return tuple(fragment for fragment in value if fragment)
