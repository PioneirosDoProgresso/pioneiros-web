#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, cast

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
    from markupsafe import Markup, escape
except ImportError as exc:
    missing = exc.name or "dependency"
    raise SystemExit(
        f"Missing {missing}. Install dependencies with: "
        "python -m pip install jinja2 pyyaml"
    ) from exc

ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "template"
VIEW_FILE = ROOT / "views" / "public.yaml"
OUTPUT_FILE = ROOT / "index.html"
INLINE_STRONG_PATTERN = re.compile(r"(\*\*|__)(.+?)\1")


def render_inline_markup(raw_text: str) -> Markup:
    escaped_text: str = str(escape(raw_text))
    formatted_text: str = INLINE_STRONG_PATTERN.sub(r"<strong>\2</strong>", escaped_text)
    formatted_text = formatted_text.replace("\n", "<br>\n")
    return Markup(formatted_text)


def transform_view_value(raw_value: Any) -> Any:
    if isinstance(raw_value, str):
        return render_inline_markup(raw_value)

    if isinstance(raw_value, list):
        transformed_list: List[Any] = [transform_view_value(item) for item in raw_value]
        return transformed_list

    if isinstance(raw_value, dict):
        transformed_dict: Dict[str, Any] = {
            key: transform_view_value(value)
            for key, value in raw_value.items()
        }
        return transformed_dict

    return raw_value


def prepare_view_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    return cast(Dict[str, Any], transform_view_value(raw_data))


def main() -> int:
    if not VIEW_FILE.is_file():
        print(f"View not found: {VIEW_FILE}", file=sys.stderr)
        return 1

    raw_data: Dict[str, Any] = cast(
        Dict[str, Any],
        yaml.safe_load(VIEW_FILE.read_text(encoding="utf-8")) or {},
    )
    data: Dict[str, Any] = prepare_view_data(raw_data)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    html = env.get_template("index.html.jinja").render(**data)
    OUTPUT_FILE.write_text(html.rstrip() + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT)} from {VIEW_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
