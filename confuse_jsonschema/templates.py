"""
Schema template classes for JSON Schema validation.

This module contains schema validation template classes that extend
Confuse templates to add JSON Schema constraint validation.
"""

import confuse
import re
from typing import Optional, List
from .formats import get_format_validator


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

        # Format validation
        if self.string_format:
            format_validator = get_format_validator(self.string_format)
            if format_validator and not format_validator(value):
                self.fail(f"must be a valid {self.string_format}", view)

        # Pattern validation is handled by parent class confuse.String
        # We only need to handle min/max length and format here since
        # pattern is passed to parent

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
        if isinstance(value, bool):
            # JSON Schema considers booleans as separate from integers
            self.fail("must be an integer, not a boolean", view)
        elif isinstance(value, float):
            # Only accept floats that are exactly integers (like 15.0)
            if value != int(value):
                self.fail("must be an integer, not a float", view)
            value = int(value)
        elif not isinstance(value, int):
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
        # JSON Schema number type accepts both integers and floats
        # but not booleans (which are a separate type in JSON Schema)
        if isinstance(value, bool):
            self.fail("must be a number, not a boolean", view)
        elif isinstance(value, (int, float)):
            # Accept both int and float directly
            pass
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


class SchemaOneOf(confuse.Template):
    """A template that validates exactly one of the provided templates
    matches."""

    def __init__(self, templates: List, default=confuse.REQUIRED):
        super().__init__(default)
        self.templates = list(templates)

    def __repr__(self):
        args = []

        if self.templates:
            args.append("templates=" + repr(self.templates))

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "SchemaOneOf({0})".format(", ".join(args))

    def convert(self, value, view):
        """Ensure that exactly one template matches the value."""
        valid_templates = []
        errors = []

        for i, template in enumerate(self.templates):
            try:
                # Use confuse's template system to validate each template
                template_obj = confuse.as_template(template)
                validated_value = template_obj.convert(value, view)
                valid_templates.append((i, validated_value))
            except confuse.ConfigError as exc:
                errors.append(f"template {i}: {str(exc)}")

        if len(valid_templates) == 0:
            self.fail(
                "must match exactly one template; no templates matched. "
                f"Errors: {'; '.join(errors)}",
                view,
            )
        elif len(valid_templates) > 1:
            matched_indices = [str(i) for i, _ in valid_templates]
            self.fail(
                f"must match exactly one template; multiple templates "
                f"matched: {', '.join(matched_indices)}",
                view,
            )

        # Return the validated value from the single matching template
        return valid_templates[0][1]


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


class SchemaObject(confuse.Template):
    """A template that validates object JSON schema constraints."""

    def __init__(
        self,
        properties_template: dict,
        additional_properties=True,
        dependent_required=None,
        dependent_templates=None,
        property_names_template=None,
        resolver=None,
        default=confuse.REQUIRED,
    ):
        super().__init__(default)
        self.properties_template = properties_template
        self.additional_properties = additional_properties
        self.dependent_required = dependent_required or {}
        self.dependent_templates = dependent_templates or {}  # Pre-compiled
        self.property_names_template = property_names_template
        self.resolver = resolver

    def __repr__(self):
        args = []
        args.append(f"properties={repr(self.properties_template)}")
        args.append(
            f"additional_properties={repr(self.additional_properties)}"
        )

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "SchemaObject({0})".format(", ".join(args))

    def convert(self, value, view):
        """Validate object with additionalProperties constraints."""
        if not isinstance(value, dict):
            self.fail("must be an object", view)

        # Validate property names if schema is provided
        if self.property_names_template is not None:
            self._validate_property_names(value, view)

        result = {}

        # Validate known properties using the properties template
        for key, template in self.properties_template.items():
            if key in value:
                try:
                    template_obj = confuse.as_template(template)
                    result[key] = template_obj.convert(value[key], view[key])
                except confuse.ConfigError as e:
                    self.fail(f"property '{key}': {str(e)}", view)
            elif not isinstance(template, confuse.Optional):
                # Required property is missing
                self.fail(f"missing required property '{key}'", view)

        # Handle additional properties
        additional_keys = (
            set(value.keys()) - set(self.properties_template.keys())
        )

        if self.additional_properties is False and additional_keys:
            additional_list = sorted(list(additional_keys))
            self.fail(
                f"additional properties not allowed: {additional_list}", view
            )
        elif isinstance(self.additional_properties, dict):
            # Validate additional properties against schema
            from .to_template import to_template
            additional_template = to_template(
                self.additional_properties, self.resolver
            )
            for key in additional_keys:
                try:
                    template_obj = confuse.as_template(additional_template)
                    result[key] = template_obj.convert(value[key], view[key])
                except confuse.ConfigError as e:
                    self.fail(f"additional property '{key}': {str(e)}", view)
        elif self.additional_properties is True:
            # Allow additional properties as-is
            for key in additional_keys:
                result[key] = value[key]

        # Validate property dependencies
        self._validate_dependent_required(value, view)
        self._validate_dependent_schemas(value, view, result)

        return result

    def _validate_dependent_required(self, value, view):
        """Validate dependentRequired constraints."""
        for trigger_prop, required_props in self.dependent_required.items():
            if trigger_prop in value:
                # If trigger property exists, check required properties exist
                missing_props = [
                    prop for prop in required_props if prop not in value
                ]
                if missing_props:
                    missing_list = sorted(missing_props)
                    self.fail(
                        f"property '{trigger_prop}' requires "
                        f"properties: {missing_list}",
                        view
                    )

    def _validate_property_names(self, value, view):
        """Validate property names against the propertyNames schema."""
        for property_name in value.keys():
            try:
                # Create a temporary configuration for property name validation
                temp_config = confuse.Configuration('temp')
                temp_config.set({'prop_name': property_name})
                property_name_view = temp_config['prop_name']
                template_obj = confuse.as_template(
                    self.property_names_template
                )
                template_obj.convert(property_name, property_name_view)
            except confuse.ConfigError as e:
                self.fail(
                    f"property name '{property_name}' is invalid: {str(e)}",
                    view
                )

    def _validate_dependent_schemas(self, value, view, result):
        """Validate dependentSchemas constraints."""
        for trigger_prop, template in self.dependent_templates.items():
            if trigger_prop in value:
                # If trigger property exists, validate the entire object
                # against the pre-compiled dependent template
                try:
                    # Use the view to validate the dependent schema template
                    # This ensures proper error handling and view context
                    view.get(template)
                except confuse.ConfigError as e:
                    self.fail(
                        f"dependent schema for property '{trigger_prop}': "
                        f"{str(e)}",
                        view
                    )


class Conditional(confuse.Template):
    """A template that validates if/then/else conditional schemas."""

    def __init__(
        self,
        if_schema: dict,
        then_schema: Optional[dict] = None,
        else_schema: Optional[dict] = None,
        resolver=None,
        default=confuse.REQUIRED,
    ):
        super().__init__(default)
        self.if_schema = if_schema
        self.then_schema = then_schema
        self.else_schema = else_schema
        self.resolver = resolver

    def __repr__(self):
        args = []
        args.append(f"if_schema={repr(self.if_schema)}")
        if self.then_schema is not None:
            args.append(f"then_schema={repr(self.then_schema)}")
        if self.else_schema is not None:
            args.append(f"else_schema={repr(self.else_schema)}")

        if self.default is not confuse.REQUIRED:
            args.append(repr(self.default))

        return "Conditional({0})".format(", ".join(args))

    def convert(self, value, view):
        """Validate using if/then/else conditional logic."""
        from .to_template import to_template

        # Always convert the 'if' schema to a template and test it
        if_template = to_template(self.if_schema, self.resolver)
        if_template_obj = confuse.as_template(if_template)

        # Test if the 'if' condition matches
        if_matches = False
        try:
            # Try to validate against the 'if' schema
            if_template_obj.convert(value, view)
            if_matches = True
        except confuse.ConfigError:
            # 'if' condition doesn't match
            if_matches = False

        # Choose the appropriate branch schema
        branch_schema = None
        if if_matches and self.then_schema is not None:
            branch_schema = self.then_schema
        elif not if_matches and self.else_schema is not None:
            branch_schema = self.else_schema

        # Apply validations - tricky part of JSON Schema if/then/else
        final_value = value
        validation_errors = []

        # JSON Schema if/then/else semantics:
        # - The 'if' schema is always applied as validation
        # - But if 'if' fails and we have 'else', validation can still succeed
        # - If 'if' succeeds and we have 'then', both 'if' and 'then' must pass

        if_validation_passed = if_matches
        try:
            final_value = if_template_obj.convert(value, view)
        except confuse.ConfigError as e:
            if_validation_passed = False
            # Only record 'if' error if we don't have an appropriate branch
            # or if the branch also fails
            if not branch_schema:
                validation_errors.append(f"if condition: {str(e)}")

        # Apply the branch schema if present
        branch_validation_passed = True
        if branch_schema is not None:
            try:
                branch_template = to_template(branch_schema, self.resolver)
                branch_template_obj = confuse.as_template(branch_template)
                final_value = branch_template_obj.convert(value, view)
            except confuse.ConfigError as e:
                branch_validation_passed = False
                branch_name = "then" if if_matches else "else"
                validation_errors.append(f"{branch_name} condition: {str(e)}")

        # Determine overall success based on JSON Schema semantics
        overall_success = True

        if if_matches:
            # 'if' condition matched
            if not if_validation_passed:
                overall_success = False
            if branch_schema and not branch_validation_passed:
                overall_success = False
        else:
            # 'if' condition did not match
            if branch_schema:
                # We have an 'else' branch - only that needs to pass
                if not branch_validation_passed:
                    overall_success = False
            else:
                # No 'else' branch - 'if' itself must pass
                if not if_validation_passed:
                    overall_success = False
                    validation_errors.append("if condition failed")

        # If validation failed overall, report errors
        if not overall_success and validation_errors:
            self.fail(
                (
                    f"conditional validation failed: "
                    f"{'; '.join(validation_errors)}"
                ),
                view,
            )

        return final_value
