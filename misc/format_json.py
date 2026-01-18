"""
Module providing functionality to format JSON data using prettier's formatting style.
"""

import json


def format_json_prettier(obj, indent=2, max_line_length=80):
    """Format JSON with prettier-style formatting."""

    def format_value(value, current_indent):
        if isinstance(value, dict):
            if not value:
                return "{}"

            lines = ["{"]
            items = list(value.items())
            for i, (k, v) in enumerate(items):
                formatted_value = format_value(v, current_indent + indent)
                comma = "," if i < len(items) - 1 else ""

                # Check if value is a simple array that fits on one line
                if isinstance(v, list) and all(
                    isinstance(x, (str, int, float, bool, type(None))) for x in v
                ):
                    json_str = json.dumps(v, ensure_ascii=False)
                    if len(json_str) <= max_line_length - current_indent - len(k) - 5:
                        formatted_value = json_str

                lines.append(
                    f"{' ' * (current_indent + indent)}{json.dumps(k)}: {formatted_value}{comma}"
                )
            lines.append(f"{' ' * current_indent}}}")
            return "\n".join(lines)

        if isinstance(value, list):
            if not value:
                return "[]"

            # Check if all items are simple and the whole array fits on one line
            if all(isinstance(x, (str, int, float, bool, type(None))) for x in value):
                json_str = json.dumps(value, ensure_ascii=False)
                if len(json_str) <= max_line_length:
                    return json_str

            # Otherwise, format with each item on a new line
            lines = ["["]
            for i, item in enumerate(value):
                formatted_item = format_value(item, current_indent + indent)
                comma = "," if i < len(value) - 1 else ""
                lines.append(
                    f"{' ' * (current_indent + indent)}{formatted_item}{comma}"
                )
            lines.append(f"{' ' * current_indent}]")
            return "\n".join(lines)

        return json.dumps(value, ensure_ascii=False)

    return format_value(obj, 0)
