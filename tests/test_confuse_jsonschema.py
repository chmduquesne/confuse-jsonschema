"""
Tests for confuse_jsonschema module.
"""

import pytest
import confuse
from confuse_jsonschema import to_template
from confuse_jsonschema.templates import (
    SchemaString,
    SchemaInteger,
    SchemaNumber,
    SchemaSequence,
    AllOf,
    Composite,
    Not,
    SchemaOneOf,
)


class TestBasicTypes:
    """Test conversion of basic JSON Schema types."""

    def test_string_schema(self):
        """Test string schema conversion."""
        schema = {"type": "string"}
        template = to_template(schema)
        assert template == str

    def test_string_with_default(self):
        """Test string schema with default value."""
        schema = {"type": "string", "default": "hello"}
        template = to_template(schema)
        assert template == "hello"

    def test_integer_schema(self):
        """Test integer schema conversion."""
        schema = {"type": "integer"}
        template = to_template(schema)
        assert isinstance(template, SchemaInteger)

    def test_integer_with_default(self):
        """Test integer schema with default value."""
        schema = {"type": "integer", "default": 42}
        template = to_template(schema)
        assert template == 42

    def test_number_schema(self):
        """Test number schema conversion."""
        schema = {"type": "number"}
        template = to_template(schema)
        assert isinstance(template, SchemaNumber)

    def test_boolean_schema(self):
        """Test boolean schema conversion."""
        schema = {"type": "boolean"}
        template = to_template(schema)
        assert template == bool

    def test_boolean_with_default(self):
        """Test boolean schema with default value."""
        schema = {"type": "boolean", "default": True}
        template = to_template(schema)
        assert template is True


class TestObjectSchemas:
    """Test conversion of object schemas."""

    def test_simple_object(self):
        """Test simple object schema conversion."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        template = to_template(schema)

        assert "name" in template
        assert "age" in template
        assert template["name"] == str
        assert isinstance(template["age"], confuse.Optional)

    def test_object_with_defaults(self):
        """Test object schema with default values."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "unnamed"},
                "port": {"type": "integer", "default": 8080},
            },
        }
        template = to_template(schema)

        assert template["name"] == "unnamed"
        assert template["port"] == 8080

    def test_nested_object(self):
        """Test nested object schema conversion."""
        schema = {
            "type": "object",
            "properties": {
                "server": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer", "default": 80},
                    },
                    "required": ["host"],
                }
            },
        }
        template = to_template(schema)

        assert "server" in template
        server_template = template["server"]
        assert isinstance(server_template, confuse.Optional)


class TestArraySchemas:
    """Test conversion of array schemas."""

    def test_array_of_strings(self):
        """Test array of strings schema conversion."""
        schema = {"type": "array", "items": {"type": "string"}}
        template = to_template(schema)

        assert isinstance(template, confuse.Sequence)

    def test_array_of_objects(self):
        """Test array of objects schema conversion."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"},
                },
                "required": ["name"],
            },
        }
        template = to_template(schema)

        assert isinstance(template, confuse.Sequence)

    def test_array_without_items(self):
        """Test array schema without items specification."""
        schema = {"type": "array"}
        template = to_template(schema)

        assert isinstance(template, confuse.Sequence)


class TestSpecialFormats:
    """Test conversion of special string formats."""

    def test_path_format(self):
        """Test path format conversion."""
        schema = {"type": "string", "format": "path"}
        template = to_template(schema)

        assert isinstance(template, confuse.Filename)

    def test_uri_reference_format(self):
        """Test URI reference format conversion."""
        schema = {"type": "string", "format": "uri-reference"}
        template = to_template(schema)

        assert isinstance(template, confuse.Filename)


class TestErrorHandling:
    """Test error handling in schema conversion."""

    def test_invalid_schema_type(self):
        """Test handling of invalid schema input."""
        with pytest.raises(ValueError, match="Schema must be a dictionary"):
            to_template("not a dict")

    def test_null_schema_type(self):
        """Test handling of null schema types."""
        schema = {"type": "null"}
        template = to_template(schema)
        assert template is None

    def test_unsupported_schema_type(self):
        """Test handling of truly unsupported schema types."""
        schema = {"type": "unknown_type"}
        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            to_template(schema)

    def test_invalid_json_schema(self):
        """Test handling of invalid JSON Schema structure."""
        # Test with invalid property type
        invalid_schema = {
            "type": "object",
            "properties": "not a dict",  # should be a dict
        }
        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            to_template(invalid_schema)

    def test_invalid_schema_type_value(self):
        """Test handling of invalid type values in schema."""
        invalid_schema = {"type": 123}  # should be a string
        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            to_template(invalid_schema)

    def test_object_without_type_but_with_properties(self):
        """Test handling of object schema without explicit type."""
        schema = {"properties": {"name": {"type": "string"}}}
        template = to_template(schema)

        assert "name" in template
        assert isinstance(template["name"], confuse.Optional)

    def test_valid_complex_json_schema(self):
        """Test that complex but valid JSON schemas are accepted."""
        # This is a more complex but valid JSON Schema
        complex_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "emails": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "minItems": 1,
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        }

        # Should not raise an exception
        template = to_template(complex_schema)

        # Basic verification that conversion worked
        assert "name" in template
        assert "age" in template
        assert "emails" in template


class TestAdvancedTypes:
    """Test advanced JSON Schema features."""

    def test_const_schema(self):
        """Test const schema conversion."""
        schema = {"const": "fixed_value"}
        template = to_template(schema)
        assert template == "fixed_value"

    def test_enum_schema(self):
        """Test enum schema conversion."""
        schema = {"enum": ["red", "green", "blue"]}
        template = to_template(schema)
        assert isinstance(template, confuse.Choice)

    def test_multiple_types(self):
        """Test schema with multiple types."""
        schema = {"type": ["string", "integer"]}
        template = to_template(schema)
        assert isinstance(template, confuse.OneOf)

    def test_anyof_schema(self):
        """Test anyOf schema conversion."""
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        template = to_template(schema)
        assert isinstance(template, confuse.OneOf)

    def test_oneof_schema(self):
        """Test oneOf schema conversion."""
        schema = {
            "oneOf": [
                {"type": "string", "maxLength": 5},
                {"type": "integer", "minimum": 10},
            ]
        }
        template = to_template(schema)
        assert isinstance(template, SchemaOneOf)

    def test_all_of(self):
        schema = {"allOf": [{"type": "string"}, {"minLength": 3}]}
        template = to_template(schema)
        # For now, allOf just returns the first schema
        assert template is not None


class TestStringConstraints:
    """Test string constraint validation."""

    def test_string_with_length_constraints(self):
        """Test string with minLength and maxLength."""
        schema = {"type": "string", "minLength": 3, "maxLength": 10}
        template = to_template(schema)
        assert isinstance(template, SchemaString)

    def test_string_with_pattern(self):
        """Test string with regex pattern."""
        schema = {"type": "string", "pattern": "^[a-z]+$"}
        template = to_template(schema)
        assert isinstance(template, SchemaString)

    def test_string_without_constraints(self):
        """Test string without constraints returns basic type."""
        schema = {"type": "string"}
        template = to_template(schema)
        assert template == str


class TestNumericConstraints:
    """Test numeric constraint validation."""

    def test_integer_with_range(self):
        """Test integer with minimum and maximum."""
        schema = {"type": "integer", "minimum": 0, "maximum": 100}
        template = to_template(schema)
        assert isinstance(template, SchemaInteger)

    def test_number_with_exclusive_bounds(self):
        """Test number with exclusive bounds."""
        schema = {
            "type": "number",
            "exclusiveMinimum": 0,
            "exclusiveMaximum": 1,
        }
        template = to_template(schema)
        assert isinstance(template, SchemaNumber)

    def test_integer_with_multiple_of(self):
        """Test integer with multipleOf constraint."""
        schema = {"type": "integer", "multipleOf": 5}
        template = to_template(schema)
        assert isinstance(template, SchemaInteger)

    def test_number_without_constraints(self):
        """Test number without constraints returns SchemaNumber."""
        schema = {"type": "number"}
        template = to_template(schema)
        assert isinstance(template, SchemaNumber)


class TestArrayConstraints:
    """Test array constraint validation."""

    def test_array_with_item_constraints(self):
        """Test array with minItems and maxItems."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5,
        }
        template = to_template(schema)
        assert isinstance(template, SchemaSequence)

    def test_array_with_unique_items(self):
        """Test array with uniqueItems constraint."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        }
        template = to_template(schema)
        assert isinstance(template, SchemaSequence)

    def test_array_without_constraints(self):
        """Test array without constraints returns basic Sequence."""
        schema = {"type": "array", "items": {"type": "string"}}
        template = to_template(schema)
        assert isinstance(template, confuse.Sequence)
        assert not isinstance(template, SchemaSequence)


class TestConditionalSchemas:
    """Test conditional schema handling."""

    def test_if_then_schema(self):
        """Test if/then conditional schema."""
        schema = {"if": {"type": "string"}, "then": {"minLength": 1}}
        template = to_template(schema)
        # Should return the 'then' schema
        assert template is not None

    def test_if_else_schema(self):
        """Test if/else conditional schema."""
        schema = {"if": {"type": "string"}, "else": {"type": "integer"}}
        template = to_template(schema)
        # Should return the 'else' schema (since no 'then')
        assert template is not None


class TestReferenceSchemas:
    """Test $ref schema handling."""

    def test_basic_ref_resolution(self):
        """Test basic $ref resolution with definitions."""
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/definitions/User"}},
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                    "required": ["name"],
                }
            },
        }

        template = to_template(schema)

        # Test with confuse validation
        import confuse

        config = confuse.Configuration("test", read=False)
        config.set({"user": {"name": "Alice", "age": 30}})

        result = config.get(template)
        assert result["user"]["name"] == "Alice"
        assert result["user"]["age"] == 30

    def test_nested_ref_resolution(self):
        """Test nested $ref resolution."""
        schema = {
            "type": "object",
            "properties": {"company": {"$ref": "#/definitions/Company"}},
            "definitions": {
                "Company": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "owner": {"$ref": "#/definitions/User"},
                    },
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            },
        }

        template = to_template(schema)

        # Test with confuse validation
        import confuse

        config = confuse.Configuration("test", read=False)
        config.set(
            {
                "company": {
                    "name": "Acme Corp",
                    "owner": {"name": "John Doe", "email": "john@acme.com"},
                }
            }
        )

        result = config.get(template)
        assert result["company"]["name"] == "Acme Corp"
        assert result["company"]["owner"]["name"] == "John Doe"
        assert result["company"]["owner"]["email"] == "john@acme.com"

    def test_ref_with_array(self):
        """Test $ref resolution in array items."""
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/User"},
                }
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                }
            },
        }

        template = to_template(schema)

        import confuse

        config = confuse.Configuration("test", read=False)
        config.set(
            {
                "users": [
                    {"name": "Alice", "age": 25},
                    {"name": "Bob", "age": 30},
                ]
            }
        )

        result = config.get(template)
        assert len(result["users"]) == 2
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][1]["name"] == "Bob"

    def test_ref_to_simple_type(self):
        """Test $ref resolution to simple types."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"$ref": "#/definitions/ID"},
                "name": {"$ref": "#/definitions/Name"},
            },
            "definitions": {
                "ID": {"type": "integer", "minimum": 1},
                "Name": {"type": "string", "minLength": 1},
            },
        }

        template = to_template(schema)

        import confuse

        config = confuse.Configuration("test", read=False)
        config.set({"id": 123, "name": "Test"})

        result = config.get(template)
        assert result["id"] == 123
        assert result["name"] == "Test"

    def test_circular_reference_detection(self):
        """Test that circular references are detected and handled."""
        schema = {
            "definitions": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "child": {"$ref": "#/definitions/Node"},
                    },
                }
            },
            "$ref": "#/definitions/Node",
        }

        # Should raise an error due to circular reference
        with pytest.raises(ValueError, match="Circular reference detected"):
            to_template(schema)

    def test_invalid_ref(self):
        """Test handling of invalid $ref."""
        schema = {
            "type": "object",
            "properties": {"user": {"$ref": "#/definitions/NonExistent"}},
            "definitions": {},
        }

        with pytest.raises(ValueError, match="Failed to resolve \\$ref"):
            to_template(schema)

    def test_ref_with_additional_properties(self):
        """Test $ref with additional properties (JSON Schema 2019-09+
        behavior)."""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "$ref": "#/definitions/User",
                    "description": "A user object",
                }
            },
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
        }

        # Should work - additional properties are merged with resolved schema
        template = to_template(schema)

        import confuse

        config = confuse.Configuration("test", read=False)
        config.set({"user": {"name": "Alice"}})

        result = config.get(template)
        assert result["user"]["name"] == "Alice"

    def test_deep_nested_pointer(self):
        """Test deep nested JSON pointer resolution."""
        schema = {
            "type": "object",
            "properties": {
                "config": {"$ref": "#/definitions/nested/deep/Config"}
            },
            "definitions": {
                "nested": {
                    "deep": {
                        "Config": {
                            "type": "object",
                            "properties": {"setting": {"type": "string"}},
                        }
                    }
                }
            },
        }

        template = to_template(schema)

        import confuse

        config = confuse.Configuration("test", read=False)
        config.set({"config": {"setting": "value"}})

        result = config.get(template)
        assert result["config"]["setting"] == "value"


class TestIntegration:
    """Integration tests with actual confuse validation."""

    def test_end_to_end_validation(self):
        """Test that generated templates work with confuse validation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "test"},
                "count": {"type": "integer", "default": 1},
                "enabled": {"type": "boolean", "default": True},
            },
        }

        template = to_template(schema)
        config = confuse.Configuration("test", read=False)

        # Should work with defaults
        result = config.get(template)
        assert result["name"] == "test"
        assert result["count"] == 1
        assert result["enabled"] is True


class TestAllOfTemplate:
    """Test the AllOf template class directly."""

    def test_allof_creation(self):
        """Test AllOf template creation."""
        templates = [str, int]
        allof = AllOf(templates)

        assert allof.templates == templates
        assert allof.default == confuse.REQUIRED

    def test_allof_with_default(self):
        """Test AllOf template with default value."""
        templates = [str, int]
        default_value = "test"
        allof = AllOf(templates, default=default_value)

        assert allof.templates == templates
        assert allof.default == default_value

    def test_allof_repr(self):
        """Test AllOf string representation."""
        templates = [str, int]
        allof = AllOf(templates)

        repr_str = repr(allof)
        assert "AllOf" in repr_str
        assert "templates=" in repr_str

    def test_allof_repr_with_default(self):
        """Test AllOf string representation with default."""
        templates = [str]
        default_value = "test"
        allof = AllOf(templates, default=default_value)

        repr_str = repr(allof)
        assert "AllOf" in repr_str
        assert "templates=" in repr_str
        assert "'test'" in repr_str


class TestAllOfSchemaConversion:
    """Test allOf schema conversion to AllOf templates."""

    def test_simple_allof_conversion(self):
        """Test simple allOf schema conversion."""
        schema = {"allOf": [{"type": "string"}, {"minLength": 3}]}
        template = to_template(schema)

        assert isinstance(template, AllOf)
        assert len(template.templates) == 2

    def test_complex_allof_conversion(self):
        """Test complex allOf schema with multiple constraints."""
        schema = {
            "allOf": [
                {"type": "string"},
                {"minLength": 3},
                {"maxLength": 10},
                {"pattern": "^[a-z]+$"},
            ]
        }
        template = to_template(schema)

        assert isinstance(template, AllOf)
        assert len(template.templates) == 4

    def test_allof_with_object_schemas(self):
        """Test allOf with object schemas."""
        schema = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                {
                    "type": "object",
                    "properties": {"age": {"type": "integer", "minimum": 0}},
                },
            ]
        }
        template = to_template(schema)

        assert isinstance(template, AllOf)
        assert len(template.templates) == 2

    def test_empty_allof_conversion(self):
        """Test empty allOf schema conversion raises error."""
        schema = {"allOf": []}

        # Empty allOf is invalid per JSON Schema spec
        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            to_template(schema)

    def test_allof_with_default_value(self):
        """Test allOf schema with default value."""
        schema = {
            "allOf": [{"type": "string"}, {"minLength": 3}],
            "default": "test",
        }
        template = to_template(schema)

        assert isinstance(template, AllOf)
        assert template.default == "test"


class TestAllOfValidation:
    """Test AllOf validation behavior with actual confuse validation."""

    def test_allof_string_constraints_success(self):
        """Test AllOf validation success with string constraints."""
        schema = {
            "allOf": [
                {"type": "string"},
                {"type": "string", "minLength": 3},
                {"type": "string", "maxLength": 10},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": "hello"})

        # Should pass validation
        result = config.get({"value": template})
        assert result["value"] == "hello"

    def test_allof_string_constraints_failure(self):
        """Test AllOf validation failure with string constraints."""
        schema = {
            "allOf": [
                {"type": "string"},
                {
                    "type": "string",
                    "minLength": 10,
                },  # This will fail for short strings
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": "short"})

        # Should fail validation
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_allof_numeric_constraints_success(self):
        """Test AllOf validation success with numeric constraints."""
        schema = {
            "allOf": [
                {"type": "integer"},
                {"type": "integer", "minimum": 1},
                {"type": "integer", "maximum": 100},
                {"type": "integer", "multipleOf": 5},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": 25})  # Valid: integer, 1-100, multiple of 5

        result = config.get({"value": template})
        assert result["value"] == 25

    def test_allof_numeric_constraints_failure(self):
        """Test AllOf validation failure with numeric constraints."""
        schema = {
            "allOf": [
                {"type": "integer"},
                {"type": "integer", "minimum": 1},
                {"type": "integer", "maximum": 100},
                {"type": "integer", "multipleOf": 5},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": 23})  # Invalid: not multiple of 5

        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_allof_mixed_type_constraints(self):
        """Test AllOf with mixed constraint types."""
        schema = {
            "allOf": [
                {"type": "string"},
                {"type": "string", "minLength": 3},
                {"type": "string", "pattern": "^[a-z]+$"},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Valid case
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Invalid case - contains uppercase
        config.set({"value": "Hello"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_allof_array_constraints(self):
        """Test AllOf with array constraints."""
        schema = {
            "allOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "array", "minItems": 2},
                {"type": "array", "maxItems": 5},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Valid case
        config.set({"value": ["a", "b", "c"]})
        result = config.get({"value": template})
        assert result["value"] == ["a", "b", "c"]

        # Invalid case - too few items
        config.set({"value": ["a"]})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})


class TestComposite:
    """Test the Composite class for combining logical operators."""

    def test_composite_creation(self):
        """Test Composite creation."""
        constraints = {
            "allOf": AllOf([str, int]),
            "oneOf": confuse.OneOf([str, int]),
        }
        composite = Composite(constraints)

        assert composite.constraints == constraints
        assert composite.default == confuse.REQUIRED

    def test_composite_repr(self):
        """Test Composite string representation."""
        constraints = {"allOf": AllOf([str])}
        composite = Composite(constraints, default="test")

        repr_str = repr(composite)
        assert "Composite" in repr_str
        assert "allOf=" in repr_str
        assert "'test'" in repr_str


class TestCombinedLogicalOperators:
    """Test schemas with multiple logical operators."""

    def test_allof_oneof_combination(self):
        """Test schema with both allOf and oneOf."""
        schema = {
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 3}],
            "oneOf": [
                {"type": "string", "maxLength": 10},
                {"type": "string", "pattern": "^[A-Z]+$"},
            ],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "allOf" in template.constraints
        assert "oneOf" in template.constraints

    def test_allof_anyof_combination(self):
        """Test schema with both allOf and anyOf."""
        schema = {
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 2}],
            "anyOf": [
                {"type": "string", "maxLength": 5},
                {"type": "string", "pattern": "^test"},
            ],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "allOf" in template.constraints
        assert "anyOf" in template.constraints

    def test_triple_logical_operators(self):
        """Test schema with allOf, oneOf, and anyOf."""
        schema = {
            "allOf": [{"type": "string"}],
            "oneOf": [{"minLength": 3}, {"maxLength": 10}],
            "anyOf": [{"pattern": "^[a-z]+$"}, {"pattern": "^[A-Z]+$"}],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert len(template.constraints) == 3
        assert "allOf" in template.constraints
        assert "oneOf" in template.constraints
        assert "anyOf" in template.constraints


class TestCombinedLogicalOperatorValidation:
    """Test validation behavior with combined logical operators."""

    def test_allof_oneof_validation_success(self):
        """Test successful validation with allOf + oneOf."""
        schema = {
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 3}],
            "oneOf": [
                {"type": "string", "maxLength": 10},
                {"type": "string", "pattern": "^[A-Z]+$"},
            ],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: meets allOf (string >= 3) AND oneOf (short string <= 10)
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should pass: meets allOf (string >= 3) AND oneOf (ALL CAPS
        # pattern > 10 chars)
        config.set({"value": "VERYLONGALLCAPS"})
        result = config.get({"value": template})
        assert result["value"] == "VERYLONGALLCAPS"

    def test_allof_oneof_validation_failure(self):
        """Test validation failures with allOf + oneOf."""
        schema = {
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 3}],
            "oneOf": [
                {"type": "string", "maxLength": 10},
                {"type": "string", "pattern": "^[A-Z]+$"},
            ],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should fail: doesn't meet allOf (too short)
        config.set({"value": "hi"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: meets allOf but not oneOf (too long AND not ALL CAPS)
        config.set({"value": "this_is_a_very_long_mixed_case_string"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_allof_anyof_validation_success(self):
        """Test successful validation with allOf + anyOf."""
        schema = {
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 2}],
            "anyOf": [
                {"type": "string", "maxLength": 5},
                {"type": "string", "pattern": "^test"},
            ],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: meets allOf AND anyOf (short string)
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should pass: meets allOf AND anyOf (starts with 'test')
        config.set({"value": "testing"})
        result = config.get({"value": template})
        assert result["value"] == "testing"

    def test_single_logical_operator_unchanged(self):
        """Test that single logical operators work as before."""
        # Single allOf should return AllOf template, not Composite
        schema = {"allOf": [{"type": "string"}, {"minLength": 3}]}
        template = to_template(schema)
        assert isinstance(template, AllOf)
        assert not isinstance(template, Composite)

        # Single oneOf should return SchemaOneOf template, not Composite
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        template = to_template(schema)
        assert isinstance(template, SchemaOneOf)
        assert not isinstance(template, Composite)


class TestEnumWithLogicalOperators:
    """Test schemas combining enum/const with logical operators."""

    def test_enum_with_allof(self):
        """Test schema with both enum and allOf."""
        schema = {
            "enum": ["test", "example", "sample"],
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "enum" in template.constraints
        assert "allOf" in template.constraints

    def test_enum_with_oneof(self):
        """Test schema with both enum and oneOf."""
        schema = {
            "enum": ["red", "green", "blue"],
            "oneOf": [
                {"type": "string", "minLength": 3},
                {"type": "string", "pattern": "^[a-z]+$"},
            ],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "enum" in template.constraints
        assert "oneOf" in template.constraints

    def test_const_alone(self):
        """Test that const alone returns the constant value."""
        schema = {"const": "fixed_value"}
        template = to_template(schema)

        # Should return the constant value directly, not Composite
        assert template == "fixed_value"
        assert not isinstance(template, Composite)

    def test_const_with_logical_operators(self):
        """Test schema with const and logical operators."""
        schema = {
            "const": "test_value",
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "const" in template.constraints
        assert "allOf" in template.constraints

    def test_enum_allof_oneof_combination(self):
        """Test schema with enum, allOf, and oneOf."""
        schema = {
            "enum": ["test", "example", "sample"],
            "allOf": [{"type": "string"}],
            "oneOf": [{"minLength": 4}, {"maxLength": 6}],
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert len(template.constraints) == 3
        assert "enum" in template.constraints
        assert "allOf" in template.constraints
        assert "oneOf" in template.constraints


class TestEnumLogicalOperatorValidation:
    """Test validation behavior with enum + logical operator combinations."""

    def test_enum_allof_validation_success(self):
        """Test successful validation with enum + allOf."""
        schema = {
            "enum": ["test", "example", "sample"],
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: in enum AND meets allOf constraints
        config.set({"value": "test"})  # 4 chars, in enum
        result = config.get({"value": template})
        assert result["value"] == "test"

        config.set({"value": "example"})  # 7 chars, in enum
        result = config.get({"value": template})
        assert result["value"] == "example"

    def test_enum_allof_validation_failure(self):
        """Test validation failures with enum + allOf."""
        schema = {
            "enum": ["test", "example", "sample"],
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should fail: not in enum (even though it meets allOf)
        config.set({"value": "other"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: in enum but doesn't meet allOf (too short)
        # Note: all enum values happen to be >= 4 chars, so this tests
        # const validation
        schema_with_short = {
            "enum": ["hi", "test", "example"],
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template_with_short = to_template(schema_with_short)
        config.set({"value": "hi"})  # in enum but < 4 chars
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template_with_short})

    def test_const_with_allof_validation(self):
        """Test validation with const + allOf combination."""
        schema = {
            "const": "test_value",
            "allOf": [{"type": "string"}, {"type": "string", "minLength": 4}],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: matches const AND meets allOf
        config.set({"value": "test_value"})
        result = config.get({"value": template})
        assert result["value"] == "test_value"

        # Should fail: doesn't match const (even though it meets allOf)
        config.set({"value": "other_value"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})


class TestSchemaConsistency:
    """Test that templates behave consistently with JSON Schema validation."""

    def _validate_with_jsonschema(
        self, schema: dict, instance
    ) -> tuple[bool, str]:
        """Validate Python instance against schema using jsonschema library."""
        import jsonschema

        try:
            jsonschema.validate(instance, schema)
            return True, ""
        except jsonschema.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Schema error: {str(e)}"

    def _validate_with_confuse(
        self, schema: dict, instance
    ) -> tuple[bool, str]:
        """Validate Python instance against schema using our template."""
        try:
            template = to_template(schema)
            config = confuse.Configuration("test", read=False)

            # Wrap the instance object under 'value' key and set it directly
            config.set({"value": instance})
            config.get({"value": template})
            return True, ""
        except Exception as e:
            return False, str(e)

    def _test_consistency(self, schema: dict, test_cases: list):
        """Test that both validators agree on all test cases."""
        for instance, expected_valid, description in test_cases:
            jsonschema_valid, jsonschema_error = (
                self._validate_with_jsonschema(schema, instance)
            )
            confuse_valid, confuse_error = self._validate_with_confuse(
                schema, instance
            )

            # Both should agree on validity
            assert jsonschema_valid == confuse_valid == expected_valid, (
                f"Validation inconsistency for {description}:\n"
                f"  Instance: {instance}\n"
                f"  Expected: {expected_valid}\n"
                f"  JSON Schema: {jsonschema_valid} ({jsonschema_error})\n"
                f"  Confuse: {confuse_valid} ({confuse_error})\n"
                f"  Schema: {schema}"
            )

    def test_string_constraints_consistency(self):
        """Test string constraint validation consistency."""
        schema = {
            "type": "string",
            "minLength": 3,
            "maxLength": 10,
            "pattern": "^[a-zA-Z]+$",
        }

        test_cases = [
            # (instance, expected_valid, description)
            ("hello", True, "valid string within constraints"),
            ("HelloWorld", True, "valid string at max length"),
            ("abc", True, "valid string at min length"),
            ("", False, "empty string (too short)"),
            ("ab", False, "string too short"),
            ("verylongstring", False, "string too long"),
            ("hello123", False, "contains numbers"),
            ("hello!", False, "contains special characters"),
            (123, False, "not a string"),
            (None, False, "null value"),
        ]

        self._test_consistency(schema, test_cases)

    def test_integer_constraints_consistency(self):
        """Test integer constraint validation consistency."""
        schema = {
            "type": "integer",
            "minimum": 10,
            "maximum": 100,
            "multipleOf": 5,
        }

        test_cases = [
            (15, True, "valid integer within constraints"),
            (10, True, "valid integer at minimum"),
            (100, True, "valid integer at maximum"),
            (50, True, "valid integer multiple of 5"),
            (5, False, "integer below minimum"),
            (105, False, "integer above maximum"),
            (12, False, "integer not multiple of 5"),
            (15.0, True, "float that is integer"),
            (15.5, False, "non-integer float"),
            ("15", False, "string representation of integer"),
            (None, False, "null value"),
        ]

        self._test_consistency(schema, test_cases)

    def test_array_constraints_consistency(self):
        """Test array constraint validation consistency."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 4,
            "uniqueItems": True,
        }

        test_cases = [
            (["a", "b"], True, "valid array with 2 items"),
            (["a", "b", "c"], True, "valid array with 3 items"),
            (["a", "b", "c", "d"], True, "valid array at max length"),
            (["a"], False, "array too short"),
            (["a", "b", "c", "d", "e"], False, "array too long"),
            (["a", "a"], False, "duplicate items"),
            (["a", 1], False, "mixed types"),
            ([1, 2], False, "wrong item type"),
            ("not array", False, "not an array"),
            ([], False, "empty array"),
        ]

        self._test_consistency(schema, test_cases)

    def test_object_constraints_consistency(self):
        """Test object constraint validation consistency."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0},
                "email": {
                    "type": "string",
                    "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                },
            },
            "required": ["name", "age"],
        }

        test_cases = [
            (
                {"name": "John", "age": 30},
                True,
                "valid object with required fields",
            ),
            (
                {"name": "John", "age": 30, "email": "john@example.com"},
                True,
                "valid object with all fields",
            ),
            ({"name": "John"}, False, "missing required field age"),
            ({"age": 30}, False, "missing required field name"),
            ({"name": "", "age": 30}, False, "invalid name (too short)"),
            ({"name": "John", "age": -1}, False, "invalid age (negative)"),
            (
                {"name": "John", "age": 30, "email": "invalid"},
                False,
                "invalid email format",
            ),
            ([], False, "not an object"),
            ("string", False, "not an object"),
            (None, False, "null value"),
        ]

        self._test_consistency(schema, test_cases)

    def test_enum_constraints_consistency(self):
        """Test enum constraint validation consistency."""
        schema = {"enum": ["red", "green", "blue", 42]}

        test_cases = [
            ("red", True, "valid enum string value"),
            ("green", True, "valid enum string value"),
            ("blue", True, "valid enum string value"),
            (42, True, "valid enum integer value"),
            ("yellow", False, "invalid enum value"),
            (43, False, "invalid enum integer"),
            (None, False, "null value"),
            ("Red", False, "case sensitive enum"),
        ]

        self._test_consistency(schema, test_cases)

    def test_allof_consistency(self):
        """Test allOf constraint validation consistency."""
        schema = {
            "allOf": [{"type": "string"}, {"minLength": 3}, {"maxLength": 10}]
        }

        test_cases = [
            ("hello", True, "valid string meeting all constraints"),
            ("abc", True, "valid string at min length"),
            ("1234567890", True, "valid string at max length"),
            ("ab", False, "string too short for minLength"),
            ("verylongstring", False, "string too long for maxLength"),
            (123, False, "not a string"),
        ]

        self._test_consistency(schema, test_cases)

    def test_oneof_consistency(self):
        """Test oneOf constraint validation consistency."""
        schema = {
            "oneOf": [
                {"type": "string", "maxLength": 5},
                {"type": "integer", "minimum": 10},
            ]
        }

        test_cases = [
            ("hello", True, "short string matches first schema only"),
            (15, True, "integer >= 10 matches second schema only"),
            (5, False, "integer < 10 matches no schemas"),
            ("toolong", False, "long string matches no schemas"),
            (3.14, False, "float matches no schemas"),
        ]

        self._test_consistency(schema, test_cases)

    def test_complex_schema_consistency(self):
        """Test complex schema with multiple constraint types."""
        schema = {
            "type": "object",
            "properties": {
                "username": {
                    "allOf": [
                        {"type": "string"},
                        {"minLength": 3},
                        {"maxLength": 20},
                        {"pattern": "^[a-zA-Z0-9_]+$"},
                    ]
                },
                "settings": {
                    "type": "object",
                    "properties": {
                        "theme": {"enum": ["light", "dark"]},
                        "notifications": {"type": "boolean"},
                    },
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                    "maxItems": 5,
                },
            },
            "required": ["username"],
        }

        test_cases = [
            (
                {
                    "username": "john_doe123",
                    "settings": {"theme": "dark", "notifications": True},
                    "tags": ["developer", "python"],
                },
                True,
                "valid complex object",
            ),
            (
                {"username": "john_doe123"},
                True,
                "valid with only required field",
            ),
            ({"username": "jo"}, False, "username too short"),
            ({"username": "john doe"}, False, "username contains space"),
            (
                {"username": "john_doe123", "settings": {"theme": "blue"}},
                False,
                "invalid theme enum value",
            ),
            (
                {"username": "john_doe123", "tags": ["tag1", "tag1"]},
                False,
                "duplicate tags",
            ),
        ]

        self._test_consistency(schema, test_cases)

    def test_oneof_overlapping_schemas_consistency(self):
        """Test oneOf with overlapping schemas - should fail when multiple
        match."""
        schema = {
            "oneOf": [
                {"type": "number"},  # Matches integers and floats
                {"type": "integer"},  # Matches integers only
            ]
        }

        test_cases = [
            (42, False, "integer matches both schemas - should fail"),
            (3.14, True, "float matches only first schema"),
            ("hello", False, "string matches no schemas"),
        ]

        self._test_consistency(schema, test_cases)


class TestNotTemplate:
    """Test the Not template class directly."""

    def test_not_creation(self):
        """Test Not template creation."""
        template = str
        not_template = Not(template)

        assert not_template.template == template
        assert not_template.default == confuse.REQUIRED

    def test_not_with_default(self):
        """Test Not template with default value."""
        template = str
        default_value = "test"
        not_template = Not(template, default=default_value)

        assert not_template.template == template
        assert not_template.default == default_value

    def test_not_repr(self):
        """Test Not string representation."""
        template = str
        not_template = Not(template)

        repr_str = repr(not_template)
        assert "Not" in repr_str
        assert "template=" in repr_str

    def test_not_repr_with_default(self):
        """Test Not string representation with default."""
        template = str
        default_value = "test"
        not_template = Not(template, default=default_value)

        repr_str = repr(not_template)
        assert "Not" in repr_str
        assert "template=" in repr_str
        assert "'test'" in repr_str


class TestNotSchemaConversion:
    """Test not schema conversion to Not templates."""

    def test_simple_not_conversion(self):
        """Test simple not schema conversion."""
        schema = {"not": {"type": "string"}}
        template = to_template(schema)

        assert isinstance(template, Not)
        assert template.template == str

    def test_complex_not_conversion(self):
        """Test complex not schema with constraints."""
        schema = {"not": {"type": "string", "minLength": 3, "maxLength": 10}}
        template = to_template(schema)

        assert isinstance(template, Not)
        assert isinstance(template.template, SchemaString)

    def test_not_with_object_schema(self):
        """Test not with object schemas."""
        schema = {
            "not": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            }
        }
        template = to_template(schema)

        assert isinstance(template, Not)
        assert isinstance(template.template, dict)

    def test_not_with_default_value(self):
        """Test not schema with default value."""
        schema = {"not": {"type": "string"}, "default": 42}
        template = to_template(schema)

        assert isinstance(template, Not)
        assert template.default == 42

    def test_not_with_multiple_constraints(self):
        """Test not combined with other constraints."""
        schema = {"not": {"type": "string"}, "type": "integer"}
        template = to_template(schema)

        # Should create a Composite with both 'not' and direct type constraint
        assert isinstance(template, Composite)
        assert "not" in template.constraints


class TestNotValidation:
    """Test Not validation behavior with actual confuse validation."""

    def test_not_string_success(self):
        """Test Not validation success (value doesn't match)."""
        schema = {"not": {"type": "string"}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": 123})  # Not a string

        # Should pass validation (123 is not a string)
        result = config.get({"value": template})
        assert result["value"] == 123

    def test_not_string_failure(self):
        """Test Not validation failure (value matches)."""
        schema = {"not": {"type": "string"}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": "hello"})  # This is a string

        # Should fail validation ('hello' is a string)
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_not_with_constraints_success(self):
        """Test Not validation with constrained schema."""
        schema = {"not": {"type": "string", "minLength": 5}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: not a string
        config.set({"value": 123})
        result = config.get({"value": template})
        assert result["value"] == 123

        # Should pass: string but too short
        config.set({"value": "hi"})
        result = config.get({"value": template})
        assert result["value"] == "hi"

    def test_not_with_constraints_failure(self):
        """Test Not validation failure with constrained schema."""
        schema = {"not": {"type": "string", "minLength": 3}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)
        config.set({"value": "hello"})  # String with length >= 3

        # Should fail validation ('hello' matches the not schema)
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_not_integer_constraints(self):
        """Test Not validation with integer constraints."""
        schema = {"not": {"type": "integer", "minimum": 10, "maximum": 100}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: not an integer
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should pass: integer but outside range
        config.set({"value": 5})
        result = config.get({"value": template})
        assert result["value"] == 5

        config.set({"value": 150})
        result = config.get({"value": template})
        assert result["value"] == 150

        # Should fail: integer within range
        config.set({"value": 50})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_not_array_constraints(self):
        """Test Not validation with array constraints."""
        schema = {"not": {"type": "array", "minItems": 2, "maxItems": 5}}
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: not an array
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should pass: array but wrong size
        config.set({"value": ["a"]})  # Too short
        result = config.get({"value": template})
        assert result["value"] == ["a"]

        config.set({"value": ["a", "b", "c", "d", "e", "f"]})  # Too long
        result = config.get({"value": template})
        assert result["value"] == ["a", "b", "c", "d", "e", "f"]

        # Should fail: array with correct size
        config.set({"value": ["a", "b", "c"]})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_not_combined_with_other_constraints(self):
        """Test Not combined with other logical operators."""
        schema = {
            "allOf": [{"type": "integer"}, {"minimum": 0}],
            "not": {"type": "integer", "maximum": 10},
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: integer >= 0 and not (integer <= 10), so integer > 10
        config.set({"value": 15})
        result = config.get({"value": template})
        assert result["value"] == 15

        # Should fail: matches the 'not' condition (integer <= 10)
        config.set({"value": 5})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: doesn't match allOf (negative integer)
        config.set({"value": -5})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})


class TestSchemaOneOfTemplate:
    """Test the SchemaOneOf template class directly."""

    def test_schema_oneof_creation(self):
        """Test SchemaOneOf template creation."""
        templates = [str, int]
        oneof = SchemaOneOf(templates)

        assert oneof.templates == templates
        assert oneof.default == confuse.REQUIRED

    def test_schema_oneof_with_default(self):
        """Test SchemaOneOf template with default value."""
        templates = [str, int]
        default_value = "test"
        oneof = SchemaOneOf(templates, default=default_value)

        assert oneof.templates == templates
        assert oneof.default == default_value

    def test_schema_oneof_repr(self):
        """Test SchemaOneOf string representation."""
        templates = [str, int]
        oneof = SchemaOneOf(templates)

        repr_str = repr(oneof)
        assert "SchemaOneOf" in repr_str
        assert "templates=" in repr_str

    def test_schema_oneof_repr_with_default(self):
        """Test SchemaOneOf string representation with default."""
        templates = [str]
        default_value = "test"
        oneof = SchemaOneOf(templates, default=default_value)

        repr_str = repr(oneof)
        assert "SchemaOneOf" in repr_str
        assert "templates=" in repr_str
        assert "'test'" in repr_str


class TestSchemaOneOfValidation:
    """Test SchemaOneOf validation behavior with actual confuse validation."""

    def test_schema_oneof_exactly_one_match_success(self):
        """Test SchemaOneOf validation with exactly one match."""
        schema = {
            "oneOf": [
                {"type": "string", "maxLength": 5},
                {"type": "integer", "minimum": 10},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: matches only first template (string <= 5)
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should pass: matches only second template (integer >= 10)
        config.set({"value": 15})
        result = config.get({"value": template})
        assert result["value"] == 15

    def test_schema_oneof_no_match_failure(self):
        """Test SchemaOneOf validation failure when no templates match."""
        schema = {
            "oneOf": [
                {"type": "string", "maxLength": 5},
                {"type": "integer", "minimum": 10},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should fail: matches no template (integer < 10)
        config.set({"value": 5})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

        # Should fail: matches no template (string > 5)
        config.set({"value": "toolong"})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

        # Should fail: matches no template (wrong type)
        config.set({"value": 3.14})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

    def test_schema_oneof_multiple_match_failure(self):
        """Test SchemaOneOf validation failure when multiple templates
        match."""
        # Create overlapping schemas where some values could match both
        schema = {
            "oneOf": [
                {"type": "number"},  # Accepts integers and floats
                {"type": "integer"},  # Accepts integers only
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should fail: integer matches both templates
        config.set({"value": 42})
        with pytest.raises(
            confuse.ConfigError, match="multiple templates matched"
        ):
            config.get({"value": template})

    def test_schema_oneof_string_constraints(self):
        """Test SchemaOneOf with string constraints."""
        schema = {
            "oneOf": [
                {"type": "string", "minLength": 1, "maxLength": 3},
                {"type": "string", "minLength": 5, "maxLength": 10},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: matches first template (short string)
        config.set({"value": "hi"})
        result = config.get({"value": template})
        assert result["value"] == "hi"

        # Should pass: matches second template (long string)
        config.set({"value": "hello"})
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should fail: matches no template (medium length)
        config.set({"value": "test"})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

    def test_schema_oneof_complex_constraints(self):
        """Test SchemaOneOf with complex constraint combinations."""
        # Use clearly non-overlapping schemas
        schema = {
            "oneOf": [
                {"type": "string", "pattern": "^user:"},
                {"type": "integer", "minimum": 100},
            ]
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: matches string pattern template only
        config.set({"value": "user:john"})
        result = config.get({"value": template})
        assert result["value"] == "user:john"

        # Should pass: matches integer template only
        config.set({"value": 150})
        result = config.get({"value": template})
        assert result["value"] == 150

        # Should fail: matches no template (string doesn't match pattern)
        config.set({"value": "admin:jane"})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

        # Should fail: matches no template (integer too small)
        config.set({"value": 50})
        with pytest.raises(confuse.ConfigError, match="no templates matched"):
            config.get({"value": template})

    def test_schema_oneof_with_allof_interaction(self):
        """Test SchemaOneOf combined with allOf constraints."""
        schema = {
            "allOf": [{"type": "string"}],
            "oneOf": [
                {"minLength": 1, "maxLength": 3},
                {"minLength": 5, "maxLength": 10},
            ],
        }
        template = to_template(schema)

        config = confuse.Configuration("test", read=False)

        # Should pass: string that matches allOf and exactly one oneOf template
        config.set({"value": "hi"})  # Matches first oneOf
        result = config.get({"value": template})
        assert result["value"] == "hi"

        config.set({"value": "hello"})  # Matches second oneOf
        result = config.get({"value": template})
        assert result["value"] == "hello"

        # Should fail: matches allOf but no oneOf templates
        config.set({"value": "test"})  # 4 chars, in the gap
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})


class TestConstWithLogicalOperators:
    """Test const combined with logical operators."""

    def test_const_with_not_impossible_constraint(self):
        """Test const + not that creates impossible constraint."""
        schema = {"const": "red", "not": {"type": "string"}}
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "const" in template.constraints
        assert "not" in template.constraints

        config = confuse.Configuration("test", read=False)

        # Should fail: 'red' matches const but violates not (it's a string)
        config.set({"value": "red"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: doesn't match const
        config.set({"value": "blue"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: doesn't match const
        config.set({"value": 123})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_const_with_not_valid_constraint(self):
        """Test const + not that allows the const value."""
        schema = {"const": 42, "not": {"type": "string"}}
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert "const" in template.constraints
        assert "not" in template.constraints

        config = confuse.Configuration("test", read=False)

        # Should pass: 42 matches const AND is not a string
        config.set({"value": 42})
        result = config.get({"value": template})
        assert result["value"] == 42

        # Should fail: doesn't match const
        config.set({"value": 43})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: doesn't match const
        config.set({"value": "hello"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

    def test_const_with_enum_and_not(self):
        """Test const + enum + not combination."""
        schema = {
            "const": 42,
            "enum": [42, "hello", True],
            "not": {"type": "string"},
        }
        template = to_template(schema)

        assert isinstance(template, Composite)
        assert len(template.constraints) == 3
        assert "const" in template.constraints
        assert "enum" in template.constraints
        assert "not" in template.constraints

        config = confuse.Configuration("test", read=False)

        # Should pass: 42 matches const, is in enum, and is not a string
        config.set({"value": 42})
        result = config.get({"value": template})
        assert result["value"] == 42

        # Should fail: in enum but doesn't match const and violates not
        config.set({"value": "hello"})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})

        # Should fail: doesn't match const (even though it's not a string)
        config.set({"value": 99})
        with pytest.raises(confuse.ConfigError):
            config.get({"value": template})
