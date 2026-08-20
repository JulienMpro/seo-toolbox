"""Registry for small, single-purpose SEO tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, get_type_hints


@dataclass
class ArgSpec:
    """Describe one command-line argument accepted by a tool."""

    name: str
    required: bool = False
    default: str | None = None
    help: str = ""
    is_flag: bool = False


@dataclass
class ToolSpec:
    """Describe and expose a registered mini-tool."""

    name: str
    fn: Callable
    description: str
    category: str
    args: list[ArgSpec]
    returns: str = "str"


REGISTRY: dict[str, ToolSpec] = {}


def register(spec: ToolSpec) -> None:
    """Register a tool, rejecting accidental duplicate names."""
    if spec.name in REGISTRY:
        raise ValueError(f"Tool already registered: {spec.name}")
    REGISTRY[spec.name] = spec


def list_tools(category: str | None = None) -> list[ToolSpec]:
    """Return registered tools sorted by category and name."""
    tools = REGISTRY.values()
    if category:
        tools = (tool for tool in tools if tool.category == category)
    return sorted(tools, key=lambda tool: (tool.category, tool.name))


def coerce_tool_args(spec: ToolSpec, raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and coerce raw values according to a tool's public arguments."""
    declared = {arg.name: arg for arg in spec.args}
    unknown = [name for name in raw if name not in declared]
    if unknown:
        raise ValueError(f"unknown argument: {unknown[0]}")

    values = dict(raw)
    for arg in spec.args:
        if arg.name not in values:
            if arg.required:
                raise ValueError(
                    f"missing required option --{arg.name.replace('_', '-')}"
                )
            if arg.is_flag:
                values[arg.name] = False
            elif arg.default is not None:
                values[arg.name] = arg.default

    hints = get_type_hints(spec.fn)
    for key, value in list(values.items()):
        target = hints.get(key, str)
        if target is bool:
            if isinstance(value, bool):
                continue
            if not isinstance(value, (str, int)):
                raise ValueError(f"--{key.replace('_', '-')} must be a boolean")
            normalized = str(value).lower()
            if normalized not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError(f"--{key.replace('_', '-')} must be a boolean")
            values[key] = normalized in {"true", "1", "yes"}
        elif target in {int, float, str}:
            try:
                values[key] = target(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"--{key.replace('_', '-')} must be a {target.__name__}"
                ) from exc
    return values


from . import (  # noqa: E402,F401
    analyzers, business_calc, calculators, checkers, converters, data_intel,
    domain_intel, generators, ia_tools, link_tools, misc, netlinking_extra,
    onpage_extra, refonte, reliquats, schema, serp_tools, strategy, youtube_tools,
)
