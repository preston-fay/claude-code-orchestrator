"""
Event Repository for persisting orchestrator events.

Stores events in JSON files for retrieval by API.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .events import EventType, OrchestratorEvent


class EventRepository:
    """Repository for persisting and retrieving orchestrator events."""

    def __init__(self, base_path: Path | str = "runs"):
        """Initialize the event repository.

        Args:
            base_path: Base directory for storing run data.
        """
        self._base_path = Path(base_path)

    def _get_events_file(self, project_id: str) -> Path:
        """Get the events file path for a project.

        Args:
            project_id: Project identifier.

        Returns:
            Path to events JSON file.
        """
        project_dir = self._base_path / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir / "events.json"

    def save_event(self, event: OrchestratorEvent) -> None:
        """Save an event to persistent storage.

        Args:
            event: Event to save.
        """
        events_file = self._get_events_file(event.project_id)

        # Load existing events
        events = self._load_events_from_file(events_file)

        # Add new event
        events.append(event.model_dump(mode="json"))

        # Write back
        with open(events_file, "w") as f:
            json.dump(events, f, indent=2, default=str)

    def get_events(
        self,
        project_id: str,
        event_type: EventType | None = None,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[OrchestratorEvent]:
        """Get events for a project.

        Args:
            project_id: Project identifier.
            event_type: Optional filter by event type.
            since: Optional filter for events after this timestamp.
            limit: Maximum number of events to return.

        Returns:
            List of events matching the criteria.
        """
        events_file = self._get_events_file(project_id)
        raw_events = self._load_events_from_file(events_file)

        # Convert to OrchestratorEvent objects
        events = []
        for raw in raw_events:
            try:
                # Handle string event_type conversion
                if isinstance(raw.get("event_type"), str):
                    raw["event_type"] = EventType(raw["event_type"])
                events.append(OrchestratorEvent(**raw))
            except (ValueError, TypeError) as e:
                # Skip malformed events
                continue

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if since:
            events = [e for e in events if e.timestamp > since]

        # Sort by timestamp (newest first for UI)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply limit
        if limit:
            events = events[:limit]

        return events

    def get_latest_events(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[OrchestratorEvent]:
        """Get the latest events for a project.

        Args:
            project_id: Project identifier.
            limit: Maximum number of events to return.

        Returns:
            List of latest events.
        """
        return self.get_events(project_id, limit=limit)

    def clear_events(self, project_id: str) -> None:
        """Clear all events for a project.

        Args:
            project_id: Project identifier.
        """
        events_file = self._get_events_file(project_id)
        if events_file.exists():
            events_file.unlink()

    def _load_events_from_file(self, events_file: Path) -> list[dict[str, Any]]:
        """Load events from a JSON file.

        Args:
            events_file: Path to events file.

        Returns:
            List of event dictionaries.
        """
        if not events_file.exists():
            return []

        try:
            with open(events_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []


# Global repository instance
_event_repository: EventRepository | None = None


def get_event_repository(base_path: Path | str = "runs") -> EventRepository:
    """Get the global event repository instance.

    Args:
        base_path: Base directory for storing run data.

    Returns:
        EventRepository instance.
    """
    global _event_repository
    if _event_repository is None:
        _event_repository = EventRepository(base_path)
    return _event_repository


def emit_event(
    event_type: EventType,
    project_id: str,
    message: str,
    phase: str | None = None,
    agent_id: str | None = None,
    **data: Any,
) -> OrchestratorEvent:
    """Convenience function to emit and persist an event.

    Args:
        event_type: Type of event.
        project_id: Project identifier.
        message: Human-readable message.
        phase: Current phase.
        agent_id: Agent identifier.
        **data: Additional event data.

    Returns:
        The created event.
    """
    event = OrchestratorEvent(
        event_type=event_type,
        project_id=project_id,
        phase=phase,
        agent_id=agent_id,
        message=message,
        data=data,
    )

    repo = get_event_repository()
    repo.save_event(event)

    return event
