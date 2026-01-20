"""Convert Eaton Network M2 Postman documentation export to OpenAPI 3.0 specification.

This script parses the Postman documentation JSON captured from:
https://documenter.getpostman.com/view/7058770/2sAYBSjt7J

And converts it to an OpenAPI 3.0 specification that can be used for:
- API documentation
- Code generation (TypedDict, Pydantic models)
- API client generation

Usage:
    python scripts/convert_postman_to_openapi.py

Input:  docs/eaton-network-m2-postman.json
Output: docs/eaton-network-m2-openapi.yaml
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


def infer_json_schema(value: Any, definitions: dict, path: str = "") -> dict:  # noqa: PLR0911
    """Infer JSON Schema from a sample value."""
    if value is None:
        return {"type": "string", "nullable": True}

    if isinstance(value, bool):
        return {"type": "boolean"}

    if isinstance(value, int):
        return {"type": "integer"}

    if isinstance(value, float):
        return {"type": "number"}

    if isinstance(value, str):
        # Check for common patterns
        if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
            return {"type": "string", "format": "date-time"}
        if re.match(r"^/rest/", value):
            return {"type": "string", "format": "uri-reference"}
        if re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            value,
            re.IGNORECASE,
        ):
            return {"type": "string", "format": "uuid"}
        return {"type": "string"}

    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": {}}
        # Infer from first item
        return {
            "type": "array",
            "items": infer_json_schema(value[0], definitions, path),
        }

    if isinstance(value, dict):
        properties = {}
        for key, val in value.items():
            # Skip @id links, they're metadata
            prop_schema = infer_json_schema(val, definitions, f"{path}.{key}")
            properties[key] = prop_schema

        return {"type": "object", "properties": properties}

    return {}


def parse_url(url: str | dict) -> tuple[str, list[dict], list[dict]]:  # noqa: PLR0912
    """Parse URL into path, query parameters, and path parameters."""
    if isinstance(url, dict):
        # Use path array if available for cleaner parsing
        path_parts = url.get("path", [])
        if path_parts:
            path = "/" + "/".join(path_parts)
        else:
            raw_url = url.get("raw", "")
            path = re.sub(r"^https?://\{\{domain\}\}", "", raw_url)
            if "?" in path:
                path = path.split("?")[0]
        query_params = url.get("query", [])
    else:
        raw_url = url
        query_params = []
        # Remove protocol and domain placeholder
        path = re.sub(r"^https?://\{\{domain\}\}", "", raw_url)
        # Remove query string from path
        if "?" in path:
            path = path.split("?")[0]

    # Normalize path
    if not path.startswith("/"):
        path = "/" + path

    # Remove trailing slash for consistency (except for root)
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Extract path parameters
    path_params = []
    new_path_parts = []

    for part in path.split("/"):
        if not part:
            continue

        # Check if it's a UUID-like string (20+ chars, alphanumeric with - or _)
        if re.match(r"^[a-zA-Z0-9_-]{20,}$", part):
            param_name = "resourceId"
            # Make unique if already used
            existing_names = [p["name"] for p in path_params]
            if param_name in existing_names:
                param_name = f"resourceId{len([n for n in existing_names if n.startswith('resourceId')]) + 1}"
            new_path_parts.append(f"{{{param_name}}}")
            path_params.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Resource identifier",
                }
            )
        # Check if it's a numeric ID
        elif re.match(r"^\d+$", part):
            # Get the previous segment as the resource name
            if new_path_parts:
                prev_segment = new_path_parts[-1].strip("{}")
                param_name = f"{prev_segment}Id"
            else:
                param_name = "id"
            new_path_parts.append(f"{{{param_name}}}")
            path_params.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": f"{prev_segment.title() if new_path_parts else 'Resource'} identifier",
                }
            )
        else:
            new_path_parts.append(part)

    path = "/" + "/".join(new_path_parts)

    # Parse query parameters
    query_param_specs = [
        {
            "name": qp.get("key", ""),
            "in": "query",
            "required": False,
            "schema": {"type": "string"},
            "description": qp.get("description", ""),
        }
        for qp in query_params
    ]

    return path, path_params, query_param_specs


def clean_description(desc: str | None) -> str:
    """Clean HTML tags from description."""
    if not desc:
        return ""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", "", desc)
    # Normalize whitespace
    clean = " ".join(clean.split())
    return clean.strip()


def extract_operation_id(method: str, path: str) -> str:
    """Generate an operation ID from method and path."""
    # Remove /rest/mbdetnrs/1.0/ prefix
    short_path = re.sub(r"^/rest/mbdetnrs/1\.0/", "", path)
    # Remove parameter placeholders
    short_path = re.sub(r"\{[^}]+\}", "", short_path)
    # Convert to camelCase
    parts = [p for p in short_path.split("/") if p]
    if not parts:
        parts = ["root"]

    # Build operation ID
    method_prefix = {
        "GET": "get",
        "POST": "create",
        "PUT": "update",
        "DELETE": "delete",
    }.get(method, method.lower())

    # CamelCase the path parts
    camel_parts = [parts[0]] + [p.title() for p in parts[1:]]
    return method_prefix + "".join(p.title() for p in camel_parts)


def parse_response_body(body: str) -> dict | None:
    """Parse response body JSON string."""
    if not body or body == '""':
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def parse_request_body(body: dict | None) -> dict | None:
    """Parse request body from Postman format."""
    if not body:
        return None
    raw = body.get("raw")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def build_openapi_spec(postman_data: dict) -> dict:  # noqa: PLR0912, PLR0915
    """Build OpenAPI 3.0 specification from Postman data."""
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": "Eaton Network-M2/M3 REST API",
            "description": (
                "REST API for Eaton Network-M2 and Network-M3 UPS management cards.\n\n"
                "This API allows monitoring and control of Eaton UPS devices through "
                "the Network Management Card. It provides access to power distribution "
                "status, alarms, measurements, and device configuration.\n\n"
                "Base path: `/rest/mbdetnrs/1.0/`\n\n"
                "Authentication: OAuth2 Bearer token obtained from `/rest/mbdetnrs/1.0/oauth2/token`"
            ),
            "version": "1.0.0",
            "contact": {"name": "Eaton", "url": "https://www.eaton.com"},
            "license": {"name": "Proprietary", "url": "https://www.eaton.com"},
        },
        "servers": [
            {
                "url": "https://{host}",
                "description": "Eaton Network-M2/M3 Card",
                "variables": {
                    "host": {
                        "default": "ups.local",
                        "description": "Hostname or IP address of the Network-M2/M3 card",
                    }
                },
            }
        ],
        "security": [{"bearerAuth": []}],
        "tags": [],
        "paths": {},
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "OAuth2 access token from /rest/mbdetnrs/1.0/oauth2/token",
                }
            },
            "schemas": {},
        },
    }

    # Track paths and their operations
    paths: dict[str, dict] = defaultdict(dict)
    definitions: dict[str, dict] = {}
    tags_set: set[str] = set()

    for item in postman_data.get("data", []):
        for example in item.get("example", []):
            request = example.get("request", {})
            method = request.get("method", "GET").upper()
            url = request.get("url", "")
            description = clean_description(request.get("description", ""))

            if not url:
                continue

            # Parse URL
            path, path_params, query_params = parse_url(url)

            # Skip log file downloads (not REST API)
            if path.startswith("/logs/"):
                continue

            # Determine tag from path
            path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
            tag = path_parts[3] if len(path_parts) >= 4 else "general"
            tags_set.add(tag)

            # Build operation
            operation_id = extract_operation_id(method, path)

            # Handle duplicate operation IDs
            base_op_id = operation_id
            counter = 1
            while any(
                operation_id in ops.get(m, {}).get("operationId", "")
                for ops in paths.values()
                for m in ops
            ):
                operation_id = f"{base_op_id}{counter}"
                counter += 1

            operation: dict[str, Any] = {
                "operationId": operation_id,
                "tags": [tag],
                "summary": example.get("name", path).split("/")[-1] or path,
                "description": description,
                "parameters": path_params + query_params,
                "responses": {},
            }

            # Parse response
            response = example.get("response", {})
            status_code = str(response.get("code", 200))
            response_body = parse_response_body(response.get("body", ""))

            response_spec: dict[str, Any] = {
                "description": response.get("status", "Successful response")
            }

            if response_body:
                schema = infer_json_schema(response_body, definitions, path)
                response_spec["content"] = {
                    "application/json": {
                        "schema": schema,
                        "example": response_body,
                    }
                }

            operation["responses"][status_code] = response_spec

            # Add default error responses
            if "401" not in operation["responses"]:
                operation["responses"]["401"] = {
                    "description": "Unauthorized - Invalid or missing authentication"
                }
            if "403" not in operation["responses"]:
                operation["responses"]["403"] = {
                    "description": "Forbidden - Insufficient permissions"
                }

            # Parse request body for POST/PUT
            if method in ("POST", "PUT"):
                request_body_data = parse_request_body(request.get("body"))
                if request_body_data:
                    schema = infer_json_schema(request_body_data, definitions, path)
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": schema,
                                "example": request_body_data,
                            }
                        },
                    }

            # Store operation
            method_lower = method.lower()
            if method_lower not in paths[path]:
                paths[path][method_lower] = operation
            else:
                # Merge examples if path+method already exists
                existing = paths[path][method_lower]
                if (
                    response_body
                    and "content" in response_spec
                    and "responses" in existing
                    and status_code in existing["responses"]
                ):
                    existing_resp = existing["responses"][status_code]
                    if "content" not in existing_resp:
                        existing_resp["content"] = response_spec["content"]

    # Sort and add tags
    openapi["tags"] = [
        {
            "name": tag,
            "description": f"{tag.replace('Service', ' Service').title()} operations",
        }
        for tag in sorted(tags_set)
    ]

    # Sort paths
    openapi["paths"] = dict(sorted(paths.items()))

    return openapi


def represent_str(dumper: yaml.Dumper, data: str) -> yaml.Node:
    """Custom string representer for multi-line strings."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def main() -> None:
    """Main entry point."""
    # Paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    input_file = repo_root / "docs" / "eaton-network-m2-postman.json"
    output_file = repo_root / "docs" / "eaton-network-m2-openapi.yaml"

    print(f"Reading Postman export from: {input_file}")

    # Load Postman data
    with input_file.open(encoding="utf-8") as f:
        postman_data = json.load(f)

    print(f"Found {len(postman_data.get('data', []))} API items")

    # Convert to OpenAPI
    openapi_spec = build_openapi_spec(postman_data)

    print(f"Generated {len(openapi_spec['paths'])} paths")
    print(f"Tags: {[t['name'] for t in openapi_spec['tags']]}")

    # Custom YAML dumper for nicer output
    yaml.add_representer(str, represent_str)

    # Write OpenAPI spec
    with output_file.open("w", encoding="utf-8") as f:
        yaml.dump(
            openapi_spec,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        )

    print(f"OpenAPI specification written to: {output_file}")

    # Print summary
    method_counts: dict[str, int] = defaultdict(int)
    for path_ops in openapi_spec["paths"].values():
        for method in path_ops:
            method_counts[method.upper()] += 1

    print("\nMethod summary:")
    for method, count in sorted(method_counts.items()):
        print(f"  {method}: {count}")


if __name__ == "__main__":
    main()
