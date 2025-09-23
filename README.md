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
- `format` - extensive format validation support via `SchemaString`
  - Special confuse formats: `path`, `uri-reference` convert to `confuse.Filename`
  - Standard formats: `email`, `date`, `date-time`, `uri`, `uuid`, `ipv4`, `ipv6`

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
- `additionalProperties` - full support via `SchemaObject`
  - `false` - additional properties forbidden
  - `true` - additional properties allowed (default)
  - schema object - additional properties validated against schema
- `default` - default values

#### Logical Operators
- `anyOf` - any schema can match using `confuse.OneOf`
- `oneOf` - exactly one schema must match using custom `SchemaOneOf` template
- `allOf` - all schemas must match using custom `AllOf` template
- `not` - value must NOT match schema using custom `Not` template

#### Schema References
- `$ref` - full JSON Pointer reference resolution with cycle detection
  - Supports internal references (e.g., `#/definitions/User`)
  - Handles nested references recursively
  - Detects and prevents circular references

#### Conditional Logic
- `if`/`then`/`else` - full conditional validation support via `Conditional` template
  - Properly evaluates `if` condition against the value
  - Applies `then` branch when condition matches
  - Applies `else` branch when condition doesn't match
  - Follows JSON Schema semantics exactly

### Partially Supported

#### Object Constraints
- `patternProperties` - recognized but not enforced
  - **Limitation**: Confuse doesn't support dynamic property validation based on key patterns
  - **Impact**: Pattern-based property validation is ignored

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

2. **Property Name Validation**
   ```json
   {
     "propertyNames": {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
   }
   ```
   No validation of dictionary key names

3. **Complex Array Validation**
   ```json
   {
     "prefixItems": [{"type": "string"}, {"type": "number"}],
     "items": false
   }
   ```
   Confuse sequences validate all items uniformly

4. **Advanced Format Validation**
   ```json
   {"type": "string", "format": "hostname"}
   ```
   Some specialized JSON Schema formats aren't supported (only common formats like `email`, `date`, `uri`, etc.)

5. **Schema Metadata**
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

### Advanced Logical Operators

```python
# oneOf - exactly one schema must match
schema_oneof = {
    "oneOf": [
        {"type": "string", "maxLength": 5},
        {"type": "integer", "minimum": 100}
    ]
}

# allOf - all schemas must match
schema_allof = {
    "allOf": [
        {"type": "string"},
        {"minLength": 2},
        {"maxLength": 10}
    ]
}

# not - value must NOT match the schema
schema_not = {
    "not": {"type": "string"}
}

template = to_template(schema_oneof)  # Uses SchemaOneOf template
```

### Schema References with $ref

```python
# Full $ref support with cycle detection
schema_with_ref = {
    "type": "object",
    "properties": {
        "user": {"$ref": "#/definitions/User"},
        "admin": {"$ref": "#/definitions/User"}
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            }
        }
    }
}

template = to_template(schema_with_ref)
```

### Format Validation Examples
```python
# Supported format validations:
{"type": "string", "format": "email"}         # Email validation
{"type": "string", "format": "date"}          # YYYY-MM-DD format
{"type": "string", "format": "date-time"}     # RFC 3339 date-time
{"type": "string", "format": "uri"}           # URI validation
{"type": "string", "format": "uuid"}          # UUID format
{"type": "string", "format": "ipv4"}          # IPv4 address
{"type": "string", "format": "ipv6"}          # IPv6 address

# Special confuse formats:
{"type": "string", "format": "path"}          # → confuse.Filename
{"type": "string", "format": "uri-reference"} # → confuse.Filename

# For unsupported formats, use pattern instead:
{"type": "string", "pattern": "^[a-zA-Z0-9-]+$"}
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
