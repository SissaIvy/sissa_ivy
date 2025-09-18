"""PitCrew Orchestration Layer

Purpose:
  Coordinate high-level workflows across ingestion, compliance evaluation,
  and remote action dispatch (executed by Mechanic). This is a placeholder
  scaffold to illustrate intended extension points.

Concepts:
  - Task: Declarative desired operation (e.g., 'recompute_compliance', 'dispatch_action')
  - Scheduler: In-memory naive scheduler for prototype usage
  - Registry: Maps task type -> handler callable

This module avoids external dependencies and keeps logic minimal for early testing.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List, Optional
import time

Handler = Callable[[dict], Any]

@dataclass
class Task:
    kind: str
    payload: dict
    created_ts: float = field(default_factory=lambda: time.time())
    id: int = 0

class TaskRegistry:
    def __init__(self) -> None:
        self._handlers: Dict[str, Handler] = {}

    def register(self, kind: str, handler: Handler) -> None:
        if kind in self._handlers:
            raise ValueError(f"handler already registered for kind={kind}")
        self._handlers[kind] = handler

    def dispatch(self, task: Task) -> Any:
        if task.kind not in self._handlers:
            raise KeyError(f"no handler for {task.kind}")
        return self._handlers[task.kind](task.payload)

class InMemoryScheduler:
    def __init__(self, registry: TaskRegistry) -> None:
        self.registry = registry
        self._queue: List[Task] = []
        self._next_id = 1

    def submit(self, kind: str, payload: Optional[dict] = None) -> Task:
        payload = payload or {}
        t = Task(kind=kind, payload=payload, id=self._next_id)
        self._next_id += 1
        self._queue.append(t)
        return t

    def run_once(self) -> int:
        processed = 0
        remaining: List[Task] = []
        for task in self._queue:
            try:
                self.registry.dispatch(task)
            except Exception:
                # For prototype: keep failing task for inspection
                remaining.append(task)
            else:
                processed += 1
        self._queue = remaining
        return processed

    def pending(self) -> List[Task]:
        return list(self._queue)

__all__ = [
    "Task",
    "TaskRegistry",
    "InMemoryScheduler",
]
