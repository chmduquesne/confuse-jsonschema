"""
Schema reference resolution for JSON Schema $ref.

This module provides functionality to resolve $ref references in JSON Schema
definitions, supporting JSON Pointer syntax and circular reference detection.
"""

import copy
from typing import Any, Dict, List
from urllib.parse import urldefrag


class SchemaResolver:
    """Resolves JSON Schema $ref references."""

    def __init__(self, root_schema: Dict[str, Any]):
        """
        Initialize resolver with root schema.

        Args:
            root_schema: The root JSON Schema document containing definitions
        """
        self.root_schema = root_schema
        self.resolution_stack: List[str] = (
            []
        )  # Track resolution path for cycle detection
        self._resolved_cache: Dict[str, Any] = {}  # Cache resolved schemas

    def resolve_ref(self, ref_uri: str) -> Dict[str, Any]:
        """
        Resolve a $ref URI to its schema definition.

        Args:
            ref_uri: The $ref URI (e.g., "#/definitions/User")

        Returns:
            The resolved schema definition

        Raises:
            ValueError: If reference cannot be resolved or causes circular
                reference
        """
        # Check cache first
        if ref_uri in self._resolved_cache:
            return self._resolved_cache[ref_uri]

        # Detect circular references
        if ref_uri in self.resolution_stack:
            cycle_path = " -> ".join(self.resolution_stack + [ref_uri])
            raise ValueError(f"Circular reference detected: {cycle_path}")

        # Only handle fragment references for now (internal references)
        uri, fragment = urldefrag(ref_uri)
        if uri:
            raise ValueError(
                f"External schema references not supported: {ref_uri}"
            )

        if not fragment:
            # Empty fragment means root schema
            resolved = self.root_schema
        else:
            # Parse JSON Pointer
            if not fragment.startswith("/"):
                raise ValueError(f"Invalid JSON Pointer fragment: #{fragment}")

            # Add to resolution stack for cycle detection
            self.resolution_stack.append(ref_uri)

            try:
                resolved = self._resolve_json_pointer(
                    fragment, self.root_schema
                )

                # Recursively resolve any $ref in the resolved schema
                resolved = self._resolve_nested_refs(resolved)

            finally:
                # Always remove from resolution stack
                self.resolution_stack.pop()

        # Cache the resolved schema
        self._resolved_cache[ref_uri] = resolved
        return resolved

    def _resolve_json_pointer(self, pointer: str, document: Any) -> Any:
        """
        Resolve a JSON Pointer within a document.

        Args:
            pointer: JSON Pointer string (e.g., "/definitions/User")
            document: Document to resolve pointer in

        Returns:
            The value at the pointer location

        Raises:
            ValueError: If pointer cannot be resolved
        """
        if not pointer.startswith("/"):
            raise ValueError(f"JSON Pointer must start with '/': {pointer}")

        # Split pointer into segments, handling empty root case
        if pointer == "/":
            return document

        segments = pointer[1:].split("/")
        current = document

        for segment in segments:
            # Unescape JSON Pointer special characters
            segment = segment.replace("~1", "/").replace("~0", "~")

            if isinstance(current, dict):
                if segment not in current:
                    raise ValueError(
                        f"Property '{segment}' not found in schema"
                    )
                current = current[segment]
            elif isinstance(current, list):
                try:
                    index = int(segment)
                    if index < 0 or index >= len(current):
                        raise ValueError(f"Array index {index} out of bounds")
                    current = current[index]
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValueError(f"Invalid array index: {segment}")
                    raise
            else:
                raise ValueError(
                    f"Cannot access property '{segment}' in non-object/array"
                )

        return current

    def _resolve_nested_refs(self, schema: Any) -> Any:
        """
        Recursively resolve any $ref found in a schema.

        Args:
            schema: Schema that may contain nested $ref

        Returns:
            Schema with all $ref resolved
        """
        if not isinstance(schema, dict):
            return schema

        # If this schema has a $ref, resolve it
        if "$ref" in schema:
            ref_uri = schema["$ref"]
            resolved_schema = self.resolve_ref(ref_uri)

            # If the original schema has other properties besides $ref,
            # merge them with the resolved schema (JSON Schema draft 2019-09+
            # behavior)
            if len(schema) > 1:
                # Create a copy to avoid modifying the original
                merged_schema = copy.deepcopy(resolved_schema)
                for key, value in schema.items():
                    if key != "$ref":
                        merged_schema[key] = value
                return self._resolve_nested_refs(merged_schema)
            else:
                return resolved_schema

        # Recursively process nested schemas
        resolved_schema = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                resolved_schema[key] = self._resolve_nested_refs(value)
            elif isinstance(value, list):
                resolved_schema[key] = [
                    (
                        self._resolve_nested_refs(item)
                        if isinstance(item, dict)
                        else item
                    )
                    for item in value
                ]
            else:
                resolved_schema[key] = value

        return resolved_schema


def resolve_schema_refs(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to resolve all $ref in a schema.

    Args:
        schema: JSON Schema document

    Returns:
        Schema with all $ref resolved
    """
    resolver = SchemaResolver(schema)
    return resolver._resolve_nested_refs(schema)
