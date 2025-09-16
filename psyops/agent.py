"""Backward compatibility shim (PsyOps -> Mechanic)

This module preserves the former 'PsyOps' agent naming by delegating to the
Mechanic action execution layer. It will be removed after one stable release
post-introduction. Use `mechanic.actions` directly instead.
"""
from __future__ import annotations
from typing import Any, Dict
import warnings

from mechanic.actions import DEFAULT_REGISTRY

_DEPRECATION = (
    "psyops.agent is deprecated; use mechanic.actions (DEFAULT_REGISTRY) directly. "
    "This shim will be removed after one stable release."
)

class PsyOpsAgent:
    def __init__(self) -> None:
        warnings.warn(_DEPRECATION, DeprecationWarning, stacklevel=2)
        self._registry = DEFAULT_REGISTRY

    def run(self, action: str, payload: Dict[str, Any]) -> Any:
        return self._registry.run(action, payload)

    def list(self) -> Dict[str, Any]:
        return {k: v for k, v in self._registry.list().items()}

DEFAULT_AGENT = PsyOpsAgent()

__all__ = ["PsyOpsAgent", "DEFAULT_AGENT"]
