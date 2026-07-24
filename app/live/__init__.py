"""Live Engine module for real-time match tracking and processing.

Architecture:
    Scheduler → Discovery → Queue → Worker → Provider → AI → Prediction → Signal → Publisher

Modules:
    engine.py        — Main LiveEngine entry point
    scheduler.py     — Periodic discovery cycle scheduler
    coordinator.py   — Orchestrates the full pipeline
    worker.py        — Processes individual matches
    queue.py         — Match processing queue
    events.py        — Event models and factory
    publisher.py     — Event broadcasting
    dispatcher.py    — Event routing to channels
    matcher.py       — Match discovery via Provider Layer
    state.py         — State registry for matches and workers
    registry.py      — Component registry
    heartbeat.py     — Health monitoring
    metrics.py       — Metrics collection
    models.py        — Pydantic models
    interfaces.py    — Abstract interfaces
    exceptions.py    — Custom exceptions
"""

from app.live.engine import LiveEngine

__all__ = ["LiveEngine"]
