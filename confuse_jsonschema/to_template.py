"""
Convert JSON Schema to Confuse templates.

This module provides functionality to convert JSON Schema definitions
into Confuse configuration templates.
"""

import confuse
import jsonschema
from typing import Any, Dict, Union, Optional
from .templates import (
    SchemaString,
    SchemaInteger,
    SchemaNumber,
    SchemaSequence,
    Array,
    AllOf,
    Composite,
    Not,
    SchemaOneOf,
    SchemaObject,
    Conditional,
)
from .resolver import SchemaResolver


def to_template(
    schema: Dict[str, Any], resolver: Optional[SchemaResolver] = None
) -> Any:
    """
    Convert a JSON Schema to a Confuse template.

    Args:
        schema: A JSON Schema dictionary
        resolver: Optional SchemaResolver for handling $ref resolution.
                 If None, a new resolver will be created from the schema.

    Returns:
        A Confuse template that can be used for configuration validation

    Raises:
        ValueError: If the schema type is not supported or if the schema
        is invalid
        jsonschema.ValidationError: If the schema is not a valid JSON
        Schema
    """
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    # Validate that the schema is a valid JSON Schema
    try:
        jsonschema.validators.validator_for(schema).check_schema(schema)
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid JSON Schema: {e.message}") from e

    # Create resolver if not provided
    if resolver is None:
        resolver = SchemaResolver(schema)

    # Collect all constraints - don't return early unless it's const alone
    constraints = {}

    # Handle const - if it's the only constraint, return it directly
    if "const" in schema:
        const_value = schema["const"]
        # If const is the only constraint, return it directly
        # (JSON Schema semantics)
        other_constraints = [
            "enum",
            "allOf",
            "anyOf",
            "oneOf",
            "not",
            "if",
            "$ref",
            "type",
        ]
        if not any(key in schema for key in other_constraints):
            return const_value
        else:
            # Otherwise create a template that validates the const
            constraints["const"] = confuse.Choice([const_value])

    # Handle enum
    if "enum" in schema:
        constraints["enum"] = confuse.Choice(schema["enum"])

    # Handle logical operators
    if "allOf" in schema:
        constraints["allOf"] = _convert_allof_schema(schema, resolver)
    if "anyOf" in schema:
        constraints["anyOf"] = _convert_anyof_schema(schema, resolver)
    if "oneOf" in schema:
        constraints["oneOf"] = _convert_oneof_schema(schema, resolver)
    if "not" in schema:
        constraints["not"] = _convert_not_schema(schema, resolver)
    if "if" in schema:
        constraints["if"] = _convert_conditional_schema(schema, resolver)

    # Handle $ref
    if "$ref" in schema:
        # If we also have other constraints, add $ref as a constraint
        if constraints:
            constraints["$ref"] = _convert_ref_schema(schema, resolver)
        else:
            return _convert_ref_schema(schema, resolver)

    schema_type = schema.get("type")

    # Handle direct type constraints
    # Add them to constraints if we have other logical operators
    type_template = None
    if isinstance(schema_type, list):
        type_template = _convert_multiple_types_schema(schema, resolver)
    elif schema_type == "object":
        type_template = _convert_object_schema(schema, resolver)
    elif schema_type == "array":
        type_template = _convert_array_schema(schema, resolver)
    elif schema_type == "string":
        type_template = _convert_string_schema(schema)
    elif schema_type == "number" or schema_type == "integer":
        type_template = _convert_number_schema(schema)
    elif schema_type == "boolean":
        type_template = _convert_boolean_schema(schema)
    elif schema_type == "null":
        type_template = _convert_null_schema(schema)
    elif schema_type is None and (
        "properties" in schema
        or "required" in schema
        or "additionalProperties" in schema
        or "dependentRequired" in schema
        or "dependentSchemas" in schema
        or "propertyNames" in schema
        or "patternProperties" in schema
    ):
        # Handle objects without explicit type (object-related constraints)
        type_template = _convert_object_schema(schema, resolver)
    elif schema_type is None:
        # Handle schemas without explicit type - try to infer from constraints
        string_constraints = ["minLength", "maxLength", "pattern", "format"]
        number_constraints = [
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
        ]
        array_constraints = [
            "minItems",
            "maxItems",
            "uniqueItems",
            "items",
            "prefixItems",
            "contains",
            "minContains",
            "maxContains",
        ]

        if any(constraint in schema for constraint in string_constraints):
            # Infer string type from string constraints
            type_template = _convert_string_schema(
                {**schema, "type": "string"}
            )
        elif any(constraint in schema for constraint in number_constraints):
            # Infer number type from numeric constraints
            type_template = _convert_number_schema(
                {**schema, "type": "number"}
            )
        elif any(constraint in schema for constraint in array_constraints):
            # Infer array type from array constraints
            type_template = _convert_array_schema(
                {**schema, "type": "array"}, resolver
            )
        # Don't create a generic template if we only have logical
        # operators - let them stand alone
    elif schema_type is not None:
        raise ValueError(f"Unsupported schema type: {schema_type}")

    # If we have a type template and other constraints, add the type as a
    # constraint
    if type_template is not None and constraints:
        constraints["type"] = type_template

    # Now decide what to return based on the constraints collected
    if len(constraints) > 1:
        return Composite(constraints, schema.get("default", confuse.REQUIRED))
    elif len(constraints) == 1:
        return list(constraints.values())[0]
    elif (
        "type_template" in locals()
    ):  # type_template was set, even if it's None
        return type_template
    else:
        # No constraints and no type - should not happen with valid schemas
        return confuse.Template(schema.get("default", confuse.REQUIRED))


def _convert_object_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Union[Dict[str, Any], SchemaObject]:
    """Convert an object schema to a Confuse template dictionary."""
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    additional_properties = schema.get("additionalProperties", True)

    # Extract dependency information (JSON Schema Draft 2020-12)
    dependent_required = schema.get("dependentRequired", {})
    dependent_schemas = schema.get("dependentSchemas", {})
    property_names = schema.get("propertyNames")

    # Pre-compile dependent schema templates to avoid circular deps
    dependent_templates = {}
    for prop_name, dependent_schema in dependent_schemas.items():
        dependent_templates[prop_name] = to_template(
            dependent_schema, resolver
        )

    # Pre-compile propertyNames template if provided
    property_names_template = None
    if property_names is not None:
        property_names_template = to_template(property_names, resolver)

    # Pre-compile patternProperties templates if provided
    pattern_properties = schema.get("patternProperties", {})
    pattern_properties_templates = {}
    for pattern_str, pattern_schema in pattern_properties.items():
        pattern_properties_templates[pattern_str] = to_template(
            pattern_schema, resolver
        )

    template = {}

    for prop_name, prop_schema in properties.items():
        prop_template = to_template(prop_schema, resolver)

        # Handle default values
        if "default" in prop_schema:
            template[prop_name] = prop_schema["default"]
        # Make optional if not in required fields
        elif prop_name not in required_fields:
            template[prop_name] = confuse.Optional(prop_template)
        else:
            template[prop_name] = prop_template

    # Handle required fields that don't have corresponding properties
    for required_field in required_fields:
        if required_field not in template:
            # Required field without a property def - any type allowed
            template[required_field] = confuse.Template()

    # Use SchemaObject if we have constraints or dependencies
    if (
        additional_properties is not True
        or dependent_required
        or dependent_templates
        or property_names_template is not None
        or pattern_properties_templates
    ):
        return SchemaObject(
            template,
            additional_properties,
            dependent_required,
            dependent_templates,
            property_names_template,
            pattern_properties_templates,
            resolver,
            schema.get("default", confuse.REQUIRED),
        )

    return template


def _convert_array_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Union[confuse.Sequence, SchemaSequence, Array]:
    """Convert an array schema to a Confuse template."""
    prefix_items = schema.get("prefixItems")
    items_schema = schema.get("items")
    min_items = schema.get("minItems")
    max_items = schema.get("maxItems")
    unique_items = schema.get("uniqueItems", False)
    contains_schema = schema.get("contains")
    min_contains = schema.get("minContains")
    max_contains = schema.get("maxContains")

    # Convert contains schema to template if present
    contains_template = None
    if contains_schema is not None:
        contains_template = to_template(contains_schema, resolver)

    # Check if this is a tuple schema (has prefixItems)
    if prefix_items is not None:
        # Convert prefixItems schemas to templates
        prefix_templates = [
            to_template(item_schema, resolver) for item_schema in prefix_items
        ]

        # Handle additional items
        additional_items_template = None
        if items_schema is False:
            additional_items_template = False
        elif items_schema is not None:
            additional_items_template = to_template(items_schema, resolver)
        # If items_schema is None/True, additional_items_template stays None

        return Array(
            prefix_templates,
            additional_items_template,
            min_items,
            max_items,
            unique_items,
            contains_template,
            min_contains,
            max_contains,
            schema.get("default", confuse.REQUIRED),
        )

    # Regular array schema (uniform items)
    if not items_schema:
        # Default to allowing any items
        item_template = confuse.Template()
    else:
        item_template = to_template(items_schema, resolver)

    # Use SchemaSequence if we have constraints
    if (
        min_items is not None
        or max_items is not None
        or unique_items
        or contains_template is not None
    ):
        return SchemaSequence(
            item_template,
            min_items,
            max_items,
            unique_items,
            contains_template,
            min_contains,
            max_contains,
        )
    else:
        return confuse.Sequence(item_template)


def _convert_string_schema(
    schema: Dict[str, Any],
) -> Union[str, confuse.Filename, SchemaString]:
    """Convert a string schema to appropriate Confuse template."""
    string_format = schema.get("format")
    min_length = schema.get("minLength")
    max_length = schema.get("maxLength")
    pattern = schema.get("pattern")
    default_value = schema.get("default", confuse.REQUIRED)

    # Handle special confuse formats first
    if string_format in ("uri-reference", "path"):
        return confuse.Filename(
            default_value
            if default_value is not confuse.REQUIRED
            else confuse.REQUIRED
        )

    # If we have constraints (including format), use SchemaString
    if (
        min_length is not None
        or max_length is not None
        or pattern is not None
        or string_format is not None
    ):
        return SchemaString(
            min_length, max_length, pattern, string_format, default_value
        )

    # Simple cases
    if default_value is not confuse.REQUIRED:
        return default_value
    else:
        return str


def _convert_number_schema(
    schema: Dict[str, Any],
) -> Union[int, float, SchemaInteger, SchemaNumber]:
    """Convert a number/integer schema to appropriate Confuse template."""
    schema_type = schema.get("type")
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_minimum = schema.get("exclusiveMinimum")
    exclusive_maximum = schema.get("exclusiveMaximum")
    multiple_of = schema.get("multipleOf")
    default_value = schema.get("default", confuse.REQUIRED)

    has_constraints = any(
        x is not None
        for x in [
            minimum,
            maximum,
            exclusive_minimum,
            exclusive_maximum,
            multiple_of,
        ]
    )

    if schema_type == "integer":
        if has_constraints or default_value is confuse.REQUIRED:
            return SchemaInteger(
                minimum,
                maximum,
                exclusive_minimum,
                exclusive_maximum,
                multiple_of,
                default_value,
            )
        else:
            return default_value
    else:  # number
        if has_constraints or default_value is confuse.REQUIRED:
            return SchemaNumber(
                minimum,
                maximum,
                exclusive_minimum,
                exclusive_maximum,
                multiple_of,
                default_value,
            )
        else:
            return default_value


def _convert_boolean_schema(schema: Dict[str, Any]) -> bool:
    """Convert a boolean schema to Confuse template."""
    if "default" in schema:
        return schema["default"]
    else:
        return bool


def _convert_null_schema(schema: Dict[str, Any]) -> Any:
    """Convert a null schema to Confuse template."""
    return None if "default" not in schema else schema["default"]


def _convert_multiple_types_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> confuse.OneOf:
    """Convert a schema with multiple types to OneOf template."""
    schema_types = schema["type"]
    templates = []

    for schema_type in schema_types:
        type_schema = schema.copy()
        type_schema["type"] = schema_type
        templates.append(to_template(type_schema, resolver))

    return confuse.OneOf(templates, schema.get("default", confuse.REQUIRED))


def _convert_allof_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Any:
    """Convert an allOf schema - all schemas must match."""
    schemas = schema["allOf"]
    if not schemas:
        return confuse.Template()

    # Convert each schema to a template
    templates = [to_template(s, resolver) for s in schemas]

    # Return AllOf template that validates against all schemas
    return AllOf(templates, schema.get("default", confuse.REQUIRED))


def _convert_anyof_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> confuse.OneOf:
    """Convert an anyOf schema - any of the schemas can match."""
    schemas = schema["anyOf"]
    templates = [to_template(s, resolver) for s in schemas]
    return confuse.OneOf(templates, schema.get("default", confuse.REQUIRED))


def _convert_oneof_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> SchemaOneOf:
    """Convert a oneOf schema - exactly one schema must match."""
    schemas = schema["oneOf"]
    templates = [to_template(s, resolver) for s in schemas]
    return SchemaOneOf(templates, schema.get("default", confuse.REQUIRED))


def _convert_not_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Not:
    """Convert a not schema - value must NOT match the schema."""
    not_schema = schema["not"]
    template = to_template(not_schema, resolver)
    return Not(template, schema.get("default", confuse.REQUIRED))


def _convert_conditional_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Any:
    """Convert an if/then/else conditional schema."""
    if_schema = schema.get("if")
    then_schema = schema.get("then")
    else_schema = schema.get("else")

    # Create Conditional with the if/then/else schemas
    return Conditional(
        if_schema,
        then_schema,
        else_schema,
        resolver,
        schema.get("default", confuse.REQUIRED),
    )


def _convert_ref_schema(
    schema: Dict[str, Any], resolver: SchemaResolver
) -> Any:
    """Convert a $ref schema - reference to another schema."""
    ref_uri = schema["$ref"]

    try:
        # Resolve the reference using the resolver
        resolved_schema = resolver.resolve_ref(ref_uri)

        # Convert the resolved schema to a template
        return to_template(resolved_schema, resolver)
    except ValueError as e:
        # If resolution fails, raise a more informative error
        raise ValueError(f"Failed to resolve $ref '{ref_uri}': {e}") from e
