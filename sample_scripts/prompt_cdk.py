"""Small CDK-like framework for constrained random prompt generation."""

from dataclasses import dataclass
from math import exp, log
from random import Random


class _FallbackLimitExceeded(Exception):
    """The exact fallback reached its deliberately small search bound."""


class _OverlapValidationLimitExceeded(Exception):
    """The deterministic conditional-overlap proof exceeded its work budget."""


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
class Dimension:
    """Reusable dimension definition."""

    name: str
    options: tuple[Option, ...]
    break_before: bool = False


def dimension(name, *options, break_before=False):
    """Create a dimension definition that can be reused across programs."""
    _validate_dimension(name, options)
    return Dimension(name, tuple(options), bool(break_before))


@dataclass(frozen=True)
class Condition:
    dimension: str
    keys: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    match: str = "all"

    def matches(self, selection):
        selected = selection.get(self.dimension)
        if selected is None:
            return False
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
class ConditionalBranch:
    trigger: Condition
    options: tuple[Option, ...]


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
                selected = self.selection.get(value)
                if selected is None:
                    continue
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


class ConditionalDimensionChain:
    """Keep a conditional dimension declaration active for one expression."""

    def __init__(self, builder):
        self.builder = builder

    def dimension(self, name, *options):
        self.builder._add_conditional_dimension(name, options)
        return self

    def __getattr__(self, name):
        return getattr(self.builder.return_target, name)


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

    def dimension(self, name, *options):
        """Add options used only while this builder's condition matches."""
        self._add_conditional_dimension(name, options)
        return ConditionalDimensionChain(self)

    def _add_conditional_dimension(self, name, options):
        name, options, break_before = _dimension_arguments(name, options)
        name = self.resolve_dimension(name)
        self.program._add_conditional_dimension(
            name,
            options,
            self.trigger,
            break_before=break_before,
        )


class PromptBlock:
    """Group fixed fragments and dimensions so related tokens stay together."""

    def __init__(self, program, name):
        self.program = program
        self.name = name

    def fixed(self, value):
        self.program._add_fixed(value)
        return self

    def dimension(self, name, *options, break_before=False):
        name, options, template_break = _dimension_arguments(name, options)
        self.program._add_dimension(
            self._scope(name),
            options,
            break_before=break_before or template_break,
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
        if dimension.startswith("program."):
            return dimension.removeprefix("program.")
        if "." in dimension:
            return dimension
        return f"{self.name}.{dimension}"


class PromptProgram:
    """Define prompt dimensions and synthesize a valid random scene."""

    _MAX_PROPOSAL_ATTEMPTS = 10_000
    _EXACT_FALLBACK_STATE_LIMIT = 10_000
    _OVERLAP_VALIDATION_WORK_LIMIT = 100_000

    def __init__(self, name):
        self.name = name
        self.dimensions = {}
        self.conditional_dimensions = {}
        self.elements = []
        self.block_names = set()
        self.rules = []

    def dimension(self, name, *options, break_before=False):
        name, options, template_break = _dimension_arguments(name, options)
        self._add_dimension(
            name,
            options,
            break_before=break_before or template_break,
        )
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
            self._condition(
                self._program_scope(dimension),
                key,
                keys,
                tag,
                tags,
                match,
            ),
            resolve_dimension=self._program_scope,
        )

    def synth(self, seed=None):
        if self.elements and self.elements[-1][0] == "break":
            raise ValueError("break_() must be followed by prompt content")

        self._validate_conditional_overlaps()
        random = Random(seed)
        conditional_maxima = self._conditional_maximum_logs()
        for _attempt in range(self._MAX_PROPOSAL_ATTEMPTS):
            selected, correction_log = self._propose(random, conditional_maxima)
            if not all(rule.accepts(selected) for rule in self.rules):
                continue
            if correction_log >= 0 or log(random.random()) <= correction_log:
                return Scene(selected, tuple(self.elements))

        selected = self._exact_fallback(random)
        if selected is None:
            rules = "\n".join(f"- {rule.describe()}" for rule in self.rules)
            raise ValueError(f"No valid prompt combinations for {self.name}:\n{rules}")

        return Scene(selected, tuple(self.elements))

    def _conditional_maximum_logs(self):
        return {
            name: max(0.0, *(
                _log_option_weight_total(branch.options) for branch in branches
            ))
            for name, branches in self.conditional_dimensions.items()
        }

    def _propose(self, random, conditional_maxima):
        selected = {}
        correction_log = 0.0
        for element_type, name in self.elements:
            if element_type != "dimension":
                continue
            if name in self.dimensions:
                selected[name] = random.choices(self.dimensions[name], weights=[
                    option.weight for option in self.dimensions[name]
                ])[0]
                continue

            matching = self._matching_conditional_branches(name, selected)
            if not matching:
                continue
            options = matching[0].options
            selected[name] = random.choices(
                options, weights=[option.weight for option in options]
            )[0]
            correction_log += (
                _log_option_weight_total(options) - conditional_maxima[name]
            )
        return selected, correction_log

    def _validate_conditional_overlaps(self):
        positions = {
            name: position
            for position, (element_type, name) in enumerate(self.elements)
            if element_type == "dimension"
        }
        domains = {
            name: frozenset(options)
            for name, options in self.dimensions.items()
        }
        domains.update({
            name: frozenset(
                option for branch in branches for option in branch.options
            )
            for name, branches in self.conditional_dimensions.items()
        })
        cache = {}
        work = [0]
        try:
            for name, branches in self.conditional_dimensions.items():
                for index, branch in enumerate(branches):
                    for other in branches[index + 1:]:
                        requirements = [
                            self._normalize_requirement(
                                branch.trigger, positions[name], positions, domains
                            ),
                            self._normalize_requirement(
                                other.trigger, positions[name], positions, domains
                            ),
                        ]
                        if None in requirements:
                            continue
                        if self._requirements_are_reachable(
                            requirements, positions, domains, cache, work
                        ):
                            raise ValueError(
                                "Multiple conditional branches matched dimension: "
                                f"{name}"
                            )
        except _OverlapValidationLimitExceeded as error:
            raise ValueError(
                f"Conditional overlap validation limit exceeded for {self.name}"
            ) from error

    def _normalize_requirement(self, condition, cutoff, positions, domains):
        if positions[condition.dimension] >= cutoff:
            return None
        allowed = frozenset(
            option
            for option in domains[condition.dimension]
            if condition.matches({condition.dimension: option})
        )
        if not allowed:
            return None
        return condition.dimension, allowed

    def _canonical_requirements(self, requirements, positions):
        merged = {}
        for name, allowed in requirements:
            if name in merged:
                allowed = merged[name] & allowed
            if not allowed:
                return None
            merged[name] = allowed
        return tuple(sorted(
            merged.items(),
            key=lambda requirement: (positions[requirement[0]], requirement[0]),
        ))

    def _requirements_are_reachable(self, requirements, positions, domains, cache, work):
        canonical = self._canonical_requirements(requirements, positions)
        if canonical is None:
            return False
        conditional = [
            requirement
            for requirement in canonical
            if requirement[0] in self.conditional_dimensions
        ]
        if not conditional:
            return True
        if canonical in cache:
            return cache[canonical]
        self._consume_overlap_validation_work(work)
        name, allowed = max(
            conditional, key=lambda requirement: positions[requirement[0]]
        )
        remaining = [requirement for requirement in canonical if requirement[0] != name]
        result = False
        for branch in self.conditional_dimensions[name]:
            for option in branch.options:
                self._consume_overlap_validation_work(work)
                if option not in allowed:
                    continue
                prerequisite = self._normalize_requirement(
                    branch.trigger, positions[name], positions, domains
                )
                if prerequisite is None:
                    continue
                if self._requirements_are_reachable(
                    [*remaining, prerequisite], positions, domains, cache, work
                ):
                    result = True
                    break
            if result:
                break
        cache[canonical] = result
        return result

    def _consume_overlap_validation_work(self, work):
        work[0] += 1
        if work[0] > self._OVERLAP_VALIDATION_WORK_LIMIT:
            raise _OverlapValidationLimitExceeded

    def _matching_conditional_branches(self, name, selection):
        matching = [
            branch
            for branch in self.conditional_dimensions[name]
            if branch.trigger.matches(selection)
        ]
        if len(matching) > 1:
            raise ValueError(
                f"Multiple conditional branches matched dimension: {name}"
            )
        return matching

    def _exact_fallback(self, random):
        selected = None
        total_weight = 0.0
        states_seen = 0

        def visit(index, selection, weight):
            nonlocal selected, total_weight, states_seen
            if index == len(self.elements):
                if states_seen >= self._EXACT_FALLBACK_STATE_LIMIT:
                    raise _FallbackLimitExceeded
                states_seen += 1
                if not all(rule.accepts(selection) for rule in self.rules):
                    return
                total_weight += weight
                if random.random() * total_weight < weight:
                    selected = selection
                return

            element_type, name = self.elements[index]
            if element_type != "dimension":
                visit(index + 1, selection, weight)
                return
            if name in self.dimensions:
                for candidate in self.dimensions[name]:
                    visit(index + 1, {**selection, name: candidate}, weight * candidate.weight)
                return
            matching = self._matching_conditional_branches(name, selection)
            if not matching:
                visit(index + 1, selection, weight)
                return
            for candidate in matching[0].options:
                visit(index + 1, {**selection, name: candidate}, weight * candidate.weight)

        try:
            visit(0, {}, 1.0)
        except _FallbackLimitExceeded as error:
            raise ValueError(
                f"No candidate found within bounded search for {self.name}; "
                "constraints may be unsatisfiable or too selective"
            ) from error
        return selected

    def _add_dimension(self, name, options, *, break_before=False):
        if name in self.dimensions or name in self.conditional_dimensions:
            raise ValueError(f"Dimension already exists: {name}")
        _validate_dimension(name, options)
        if break_before:
            self._add_break()
        self.dimensions[name] = tuple(options)
        self.elements.append(("dimension", name))

    def _add_conditional_dimension(
        self,
        name,
        options,
        trigger,
        *,
        break_before=False,
    ):
        if name in self.dimensions:
            raise ValueError(f"Dimension already exists: {name}")
        _validate_dimension(name, options)
        if name not in self.conditional_dimensions:
            if break_before:
                raise ValueError(
                    "Conditional dimensions use option(break_before=True)"
                )
            self.conditional_dimensions[name] = []
            self.elements.append(("dimension", name))
        self.conditional_dimensions[name].append(
            ConditionalBranch(trigger, tuple(options))
        )

    def _add_fixed(self, value):
        normalized = _normalize_fragments(value, "fixed")
        fragments = [normalized] if isinstance(normalized, str) else normalized
        for fragment in fragments:
            if fragment:
                self.elements.append(("fixed", fragment))

    def _add_break(self):
        self.elements.append(("break", None))

    def _condition(self, dimension, key, keys, tag, tags, match):
        if (
            dimension not in self.dimensions
            and dimension not in self.conditional_dimensions
        ):
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

    @staticmethod
    def _program_scope(dimension):
        return dimension.removeprefix("program.")


def _dimension_arguments(name, options):
    if not isinstance(name, Dimension):
        return name, options, False
    if options:
        raise TypeError(
            "A reusable Dimension cannot be combined with additional options"
        )
    return name.name, name.options, name.break_before


def _validate_dimension(name, options):
    if not isinstance(name, str):
        raise TypeError("Dimension name must be a string")
    if not options:
        raise ValueError(f"Dimension must contain at least one option: {name}")
    if any(not isinstance(value, Option) for value in options):
        raise TypeError("Dimension options must be created with option()")


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


def _log_option_weight_total(options):
    """Return log(sum(weights)) without overflowing or underflowing first."""
    log_weights = [log(option.weight) for option in options]
    maximum = max(log_weights)
    return maximum + log(sum(exp(weight - maximum) for weight in log_weights))
