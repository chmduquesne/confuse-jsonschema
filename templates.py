"""
Schema template classes for JSON Schema validation.

This module contains schema validation template classes that extend
Confuse templates to add JSON Schema constraint validation.
"""

import confuse
import re
from typing import Optional, List


class SchemaString(confuse.String):
    """A string template that validates JSON schema constraints."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        string_format: Optional[str] = None,
        default=confuse.REQUIRED,
    ):
        # Pass pattern to parent class - it expects regex parameter
        super().__init__(default, pattern=pattern)
        self.min_length = min_length
        self.max_length = max_length
        self.json_pattern = re.compile(pattern) if pattern else None
        self.string_format = string_format

    def convert(self, value, view):
        value = super().convert(value, view)

        if self.min_length is not None and len(value) < self.min_length:
            self.fail(
                f"must be at least {self.min_length} characters long", view
            )

        if self.max_length is not None and len(value) > self.max_length:
            self.fail(
                f"must be at most {self.max_length} characters long", view
            )

        # Pattern validation is handled by parent class confuse.String
        # We only need to handle min/max length here since pattern is
        # passed to parent

        return value


class SchemaInteger(confuse.Integer):
    """An integer template that validates JSON schema constraints."""

    def __init__(
        self,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        exclusive_minimum: Optional[int] = None,
        exclusive_maximum: Optional[int] = None,
        multiple_of: Optional[int] = None,
        default=confuse.REQUIRED,
    ):
        super().__init__(default)
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of

    def convert(self, value, view):
        # JSON Schema integer type requires strict integer validation
        # Unlike confuse.Integer which accepts floats, we need to reject
        # non-integers
        if not isinstance(value, int) or isinstance(value, bool):
            if isinstance(value, float):
                # Only accept floats that are actually integers (like 15.0)
                if value != int(value):
                    self.fail("must be an integer", view)
                value = int(value)
            else:
                # Let parent handle other conversions and type errors
                value = super().convert(value, view)

        if self.minimum is not None and value < self.minimum:
            self.fail(f"must be at least {self.minimum}", view)

        if self.maximum is not None and value > self.maximum:
            self.fail(f"must be at most {self.maximum}", view)

        if (
            self.exclusive_minimum is not None
            and value <= self.exclusive_minimum
        ):
            self.fail(f"must be greater than {self.exclusive_minimum}", view)

        if (
            self.exclusive_maximum is not None
            and value >= self.exclusive_maximum
        ):
            self.fail(f"must be less than {self.exclusive_maximum}", view)

        if self.multiple_of is not None and value % self.multiple_of != 0:
            self.fail(f"must be a multiple of {self.multiple_of}", view)

        return value


class SchemaNumber(confuse.Number):
    """A number template that validates JSON schema constraints."""

    def __init__(
        self,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        exclusive_minimum: Optional[float] = None,
        exclusive_maximum: Optional[float] = None,
        multiple_of: Optional[float] = None,
        default=confuse.REQUIRED,
    ):
        super().__init__(default)
        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of

    def convert(self, value, view):
        value = super().convert(value, view)

        if self.minimum is not None and value < self.minimum:
            self.fail(f"must be at least {self.minimum}", view)

        if self.maximum is not None and value > self.maximum:
            self.fail(f"must be at most {self.maximum}", view)

        if (
            self.exclusive_minimum is not None
            and value <= self.exclusive_minimum
        ):
            self.fail(f"must be greater than {self.exclusive_minimum}", view)

        if (
            self.exclusive_maximum is not None
            and value >= self.exclusive_maximum
        ):
            self.fail(f"must be less than {self.exclusive_maximum}", view)

        if self.multiple_of is not None and value % self.multiple_of != 0:
            self.fail(f"must be a multiple of {self.multiple_of}", view)

        return value


class SchemaSequence(confuse.Sequence):
    """A sequence template that validates array JSON schema constraints."""

    def __init__(
        self,
        subtemplate,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
        unique_items: bool = False,
    ):
        super().__init__(subtemplate)
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items

    def value(self, view, template=None):
        # Get the list using parent logic
        out = super().value(view, template)

        if self.min_items is not None and len(out) < self.min_items:
            self.fail(f"must have at least {self.min_items} items", view)

        if self.max_items is not None and len(out) > self.max_items:
            self.fail(f"must have at most {self.max_items} items", view)

        if self.unique_items:
            # Handle uniqueness validation for potentially non-hashable items
            seen = []
            for item in out:
                if item in seen:
                    self.fail("all items must be unique", view)
                seen.append(item)

        return out

    def convert(self, value, view):
        value = super().convert(value, view)

        if self.min_items is not None and len(value) < self.min_items:
            self.fail(f"must have at least {self.min_items} items", view)

        if self.max_items is not None and len(value) > self.max_items:
            self.fail(f"must have at most {self.max_items} items", view)

        if self.unique_items:
            # Handle uniqueness validation for potentially non-hashable items
            seen = []
            for item in value:
                if item in seen:
                    self.fail("all items must be unique", view)
                seen.append(item)

        return value


class AllOf(confuse.Template):
    """A template validating that a value matches all provided templates."""

    def __init__(self, templates: List, default=confuse.REQUIRED):
        super().__init__(default)
        self.templates = list(templates)

    def __repr__(self):
        args = []

        if self.templates:
            args.append("templates=" + repr(self.templates))

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "AllOf({0})".format(", ".join(args))

    def convert(self, value, view):
        """Ensure that the value follows all templates."""
        errors = []
        final_value = value

        for template in self.templates:
            try:
                # Use confuse's template system to validate each template
                template_obj = confuse.as_template(template)
                # Each template validates the original value
                validated_value = template_obj.convert(value, view)
                # Keep the validated value from the last successful template
                final_value = validated_value
            except confuse.ConfigError as exc:
                errors.append(str(exc))

        if errors:
            self.fail(
                "must match all templates; failures: {0}".format(
                    "; ".join(errors)
                ),
                view,
            )

        return final_value


class Composite(confuse.Template):
    """A template that combines multiple constraints."""

    def __init__(self, constraints: dict, default=confuse.REQUIRED):
        super().__init__(default)
        self.constraints = constraints

    def __repr__(self):
        args = []
        for constraint_name, template in self.constraints.items():
            args.append(f"{constraint_name}={repr(template)}")

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "Composite({0})".format(", ".join(args))

    def convert(self, value, view):
        """Ensure that the value satisfies all constraints."""
        errors = []
        final_value = value

        for constraint_name, template in self.constraints.items():
            try:
                # Use confuse's view.get() method to validate each constraint
                final_value = view.get(template)
            except confuse.ConfigError as exc:
                errors.append(f"{constraint_name} failed: {str(exc)}")

        if errors:
            self.fail(
                "must satisfy all constraints; failures: {0}".format(
                    "; ".join(errors)
                ),
                view,
            )

        return final_value


class Not(confuse.Template):
    """A template that validates a value does NOT match the template."""

    def __init__(self, template, default=confuse.REQUIRED):
        super().__init__(default)
        self.template = template

    def __repr__(self):
        args = []

        if self.template:
            args.append("template=" + repr(self.template))

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "Not({0})".format(", ".join(args))

    def convert(self, value, view):
        """Ensure that the value does NOT match the template."""
        # Use confuse's template system to validate the template
        template_obj = confuse.as_template(self.template)

        template_validation_failed = False
        try:
            template_obj.value(view)
        except confuse.ConfigError:
            # Template validation failed, which is what we want for 'not'
            template_validation_failed = True

        if not template_validation_failed:
            # Template validation succeeded, which means 'not' should fail
            self.fail(f"must not match the template {self.template}", view)

        return value
