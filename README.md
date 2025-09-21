# confuse-jsonschema

[![codecov](https://codecov.io/gh/chmduquesne/confuse-jsonschema/branch/main/graph/badge.svg)](https://codecov.io/gh/chmduquesne/confuse-jsonschema)
[![CI](https://github.com/chmduquesne/confuse-jsonschema/actions/workflows/ci.yml/badge.svg)](https://github.com/chmduquesne/confuse-jsonschema/actions/workflows/ci.yml)

Convert JSON Schema to Confuse templates for seamless configuration validation.

## Overview

`confuse-jsonschema` is a library that allows you to create a
[Confuse](https://confuse.readthedocs.io) template from a JSON schema.
This allows you to benefit from the advanced validation capabilities of
JSON schema for checking your configuration, while taking advantage of the
flexibility of confuse for configuration management.

## Installation

```bash
pip install confuse-jsonschema
```

## Quick Start

```python
from confuse_jsonschema import to_template
import confuse

# Define your configuration schema
schema = {
    "type": "object",
    "properties": {
        "server": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "default": "localhost"},
                "port": {"type": "integer", "default": 8080}
            },
            "required": ["host"]
        },
        "database": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "timeout": {"type": "number", "default": 30.0}
            },
            "required": ["url"]
        }
    },
    "required": ["server", "database"]
}

# Convert to Confuse template
template = to_template(schema)

# Use with Confuse
config = confuse.Configuration('myapp')
validated_config = config.get(template)
```

## Supported JSON Schema Features

### Fully Supported

#### Basic Types
- `string` - converts to `str` or custom `SchemaString` with constraints
- `integer` - converts to `int` or custom `SchemaInteger` with constraints
- `number` - converts to `float` or custom `SchemaNumber` with constraints
- `boolean` - converts to `bool` or default value
- `null` - converts to `None` or default value

#### Advanced Types
- `const` - fixed constant values
- `enum` - choice from enumerated values using `confuse.Choice`
- Multiple types (e.g., `["string", "integer"]`) - converts to `confuse.OneOf`

#### Complex Types
- `object` - converts to nested dictionary template
- `array` - converts to `confuse.Sequence` or `SchemaSequence` with constraints

#### String Constraints
- `minLength` / `maxLength` - enforced via `SchemaString`
- `pattern` - regex validation via `SchemaString`
- `format` - special formats like `path`, `uri-reference` convert to `confuse.Filename`

#### Numeric Constraints
- `minimum` / `maximum` - inclusive bounds via `SchemaInteger`/`SchemaNumber`
- `exclusiveMinimum` / `exclusiveMaximum` - exclusive bounds
- `multipleOf` - divisibility validation

#### Array Constraints
- `minItems` / `maxItems` - size validation via `SchemaSequence`
- `uniqueItems` - uniqueness validation via `SchemaSequence`
- `items` - item type specification

#### Object Features
- `properties` - property definitions
- `required` - required properties (others become `confuse.Optional`)
- `default` - default values

#### Logical Operators
- `anyOf` - any schema can match using `confuse.OneOf`
- `oneOf` - exactly one schema must match using `confuse.OneOf`
- `allOf` - all schemas must match using custom `AllOf` template
- `if`/`then`/`else` - basic conditional support

###  Partially Supported

#### References
- `$ref` - basic placeholder support (returns generic `confuse.Template`)
  - **Limitation**: No actual reference resolution implemented
  - **Workaround**: Manually inline referenced schemas

#### Object Constraints
- `additionalProperties` - recognized but not enforced
  - **Limitation**: Confuse templates use fixed dictionary structures
  - **Impact**: Additional properties will be accepted without validation

- `patternProperties` - recognized but not enforced
  - **Limitation**: Confuse doesn't support dynamic property validation based on key patterns
  - **Impact**: Pattern-based property validation is ignored

#### Complex Logic
- `if`/`then`/`else` - basic implementation
  - **Limitation**: Doesn't evaluate conditions; just uses `then` or `else`
  - **Impact**: Conditional validation doesn't work properly

### Not Supported

#### Advanced JSON Schema Features

1. **Property Dependencies**
   ```json
   {
     "dependencies": {
       "credit_card": ["billing_address"]
     }
   }
   ```
   No concept of field interdependencies

2. **Conditional Validation**
   ```json
   {
     "if": {"properties": {"type": {"const": "credit_card"}}},
     "then": {"required": ["number", "cvv"]}
   }
   ```
   Dynamic validation based on other field values isn't supported

3. **Complex Array Validation**
   ```json
   {
     "prefixItems": [{"type": "string"}, {"type": "number"}],
     "items": false
   }
   ```
   Confuse sequences validate all items uniformly

4. **Property Name Validation**
   ```json
   {
     "propertyNames": {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
   }
   ```
   No validation of dictionary key names

5. **Format Validation**
   ```json
   {"type": "string", "format": "email"}
   ```
   Most JSON Schema formats aren't supported (only `path` and `uri-reference`)

6. **Schema Metadata**
   - `title`, `description`, `examples` - ignored (no impact on validation)
   - `$id`, `$schema` - ignored
   - `deprecated` - ignored

#### Limitations

1. **Configuration Layering Conflicts**
   - JSON Schema defines single validation rules
   - Confuse merges multiple configuration sources
   - **Impact**: Schema validation happens after configuration merging

2. **Type Coercion Differences**
   - JSON Schema: strict type validation
   - Confuse: automatic type coercion (e.g., string "123" → integer 123)
   - **Impact**: Some invalid values might be accepted after coercion

3. **Error Reporting**
   - JSON Schema: detailed validation error paths
   - Confuse: simpler error messages
   - **Impact**: Less precise error information for complex schemas

4. **Runtime vs Static Validation**
   - JSON Schema: can validate any data structure
   - Confuse: designed for configuration files with known structure
   - **Impact**: Less flexibility for dynamic data validation

## Examples

### Simple Configuration

```python
schema = {
    "type": "object",
    "properties": {
        "app_name": {"type": "string", "default": "MyApp"},
        "debug": {"type": "boolean", "default": False},
        "port": {"type": "integer", "default": 3000}
    }
}

template = to_template(schema)
```

### Workarounds for Unsupported Features

```python
# Instead of $ref, inline the schema
# Not supported:
schema_with_ref = {
    "type": "object",
    "properties": {
        "user": {"$ref": "#/definitions/User"}
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
    }
}

# Use this instead:
schema_inlined = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
    }
}
```

### Format Validation
```python
# Most formats aren't supported - use pattern instead
# Not supported:
{"type": "string", "format": "email"}

# Use pattern instead:
{"type": "string", "pattern": "^[^@]+@[^@]+\\.[^@]+$"}

# Supported formats:
{"type": "string", "format": "path"}        # → confuse.Filename
{"type": "string", "format": "uri-reference"}  # → confuse.Filename
```

## Development

### Setup

```bash
git clone https://github.com/chmduquesne/confuse-jsonschema.git
cd confuse-jsonschema
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
flake8
```

## Publishing to PyPI

1. Build the package:
```bash
python -m build
```

2. Upload to PyPI:
```bash
python -m twine upload dist/*
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
.
