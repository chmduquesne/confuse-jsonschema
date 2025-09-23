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
- `minItems` / `maxItems` - size validation via `SchemaSequence` or `Array`
- `uniqueItems` - uniqueness validation via `SchemaSequence` or `Array`
- `items` - item type specification for uniform arrays
- `prefixItems` - tuple validation via `Array`
  - Validates specific array positions with different schemas
  - Supports partial tuples (fewer items than prefixItems)
  - Works with `items` for additional items beyond prefix
  - Setting `items: false` disallows additional items
- `contains` - content validation via `SchemaSequence` or `Array`
  - Requires at least one array item to match the specified schema
  - Default behavior: minimum 1 match required
- `minContains` - minimum matches for `contains` schema
  - When omitted, defaults to 1 (JSON Schema specification)
  - Setting to 0 allows zero matches
- `maxContains` - maximum matches for `contains` schema
  - Combined with `minContains` for precise match count control

#### Object Features
- `properties` - property definitions
- `required` - required properties (others become `confuse.Optional`)
- `additionalProperties` - full support via `SchemaObject`
  - `false` - additional properties forbidden
  - `true` - additional properties allowed (default)
  - schema object - additional properties validated against schema
- `dependentRequired` - property dependencies via `SchemaObject`
  - When specified property exists, required properties must also be present
- `dependentSchemas` - schema dependencies via `SchemaObject`
  - When specified property exists, entire object must validate against dependent schema
- `propertyNames` - property name validation via `SchemaObject`
  - Validates all object property names against a schema
  - Supports all string constraints: pattern, format, length, enum
- `patternProperties` - pattern-based property validation via `SchemaObject`
  - Validates property values based on regex pattern matching of property names
  - Works with `properties` and `additionalProperties`
  - First matching pattern wins if multiple patterns match
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

### Not Supported

#### Advanced JSON Schema Features

1. **Advanced Format Validation**
   ```json
   {"type": "string", "format": "hostname"}
   ```
   Some specialized JSON Schema formats aren't supported (only common formats like `email`, `date`, `uri`, etc.)

2. **Schema Metadata**
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
