"""Mechanic Action Execution Layer

Provides a simple registry for endpoint or fleet-level actions.
Each action is a callable taking a dict payload and returning a result
object (any serializable value). This is intentionally minimal.
"""
from __future__ import annotations
from typing import Callable, Dict, Any

Action = Callable[[dict], Any]

class ActionRegistry:
    def __init__(self) -> None:
        self._actions: Dict[str, Action] = {}

    def register(self, name: str, action: Action) -> None:
        if name in self._actions:
            raise ValueError(f"action already registered: {name}")
        self._actions[name] = action

    def run(self, name: str, payload: dict) -> Any:
        if name not in self._actions:
            raise KeyError(f"unknown action: {name}")
        return self._actions[name](payload)

    def list(self) -> Dict[str, Action]:
        return dict(self._actions)

# Example built-in action for demonstration.
def echo_action(payload: dict) -> dict:
    return {"echo": payload}

# Instantiate a default registry and register the echo action.
DEFAULT_REGISTRY = ActionRegistry()
DEFAULT_REGISTRY.register("echo", echo_action)

__all__ = [
    "ActionRegistry",
    "echo_action",
    "DEFAULT_REGISTRY",
]
