"""Centralized StateManager for Telegram bot.

Provides FSM (Finite State Machine) management, isolated from handlers.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class State(Enum):
    """FSM states."""

    NONE = auto()
    WAITING_INPUT = auto()
    CONFIRMING = auto()
    SELECTING = auto()


@dataclass
class UserState:
    """User's FSM state."""

    state: State = State.NONE
    data: dict[str, Any] = field(default_factory=dict)
    history: list[State] = field(default_factory=list)


class StateManager:
    """Centralized FSM state manager."""

    def __init__(self) -> None:
        """Initialize state manager."""
        self._states: dict[int, UserState] = {}

    def get_state(self, user_id: int) -> State:
        """Get current state for user.

        Args:
            user_id: User ID.

        Returns:
            Current state.
        """
        if user_id not in self._states:
            self._states[user_id] = UserState()
        return self._states[user_id].state

    def set_state(self, user_id: int, state: State, **data: Any) -> None:
        """Set state for user.

        Args:
            user_id: User ID.
            state: New state.
            **data: Additional state data.
        """
        if user_id not in self._states:
            self._states[user_id] = UserState()

        user_state = self._states[user_id]
        user_state.history.append(user_state.state)
        user_state.state = state
        user_state.data.update(data)

    def get_data(self, user_id: int) -> dict[str, Any]:
        """Get state data for user.

        Args:
            user_id: User ID.

        Returns:
            State data dictionary.
        """
        if user_id not in self._states:
            return {}
        return dict(self._states[user_id].data)

    def update_data(self, user_id: int, **data: Any) -> None:
        """Update state data for user.

        Args:
            user_id: User ID.
            **data: Data to update.
        """
        if user_id not in self._states:
            self._states[user_id] = UserState()
        self._states[user_id].data.update(data)

    def clear_state(self, user_id: int) -> None:
        """Clear state for user.

        Args:
            user_id: User ID.
        """
        self._states.pop(user_id, None)

    def go_back(self, user_id: int) -> State:
        """Go back to previous state.

        Args:
            user_id: User ID.

        Returns:
            Previous state.
        """
        if user_id not in self._states:
            return State.NONE

        user_state = self._states[user_id]
        if user_state.history:
            user_state.state = user_state.history.pop()
        else:
            user_state.state = State.NONE

        return user_state.state

    def is_in_state(self, user_id: int, state: State) -> bool:
        """Check if user is in specific state.

        Args:
            user_id: User ID.
            state: State to check.

        Returns:
            True if user is in the state.
        """
        return self.get_state(user_id) == state


# Global state manager instance
state_manager = StateManager()
