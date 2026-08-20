"""Registry for small, single-purpose SEO tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


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


from . import (  # noqa: E402,F401
    analyzers, business_calc, calculators, checkers, converters, data_intel,
    domain_intel, generators, ia_tools, link_tools, misc, netlinking_extra,
    onpage_extra, refonte, reliquats, schema, serp_tools, strategy, youtube_tools,
)
