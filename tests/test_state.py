"""Tests for StateManager."""

import pytest

from app.telegram.state import State, StateManager


@pytest.fixture
def state_mgr() -> StateManager:
    """Create a fresh StateManager for each test."""
    return StateManager()


class TestStateManager:
    """Tests for StateManager."""

    def test_get_initial_state(self, state_mgr: StateManager) -> None:
        """Test getting initial state."""
        state = state_mgr.get_state(123)
        assert state == State.NONE

    def test_set_state(self, state_mgr: StateManager) -> None:
        """Test setting state."""
        state_mgr.set_state(123, State.WAITING_INPUT)
        assert state_mgr.get_state(123) == State.WAITING_INPUT

    def test_set_state_with_data(self, state_mgr: StateManager) -> None:
        """Test setting state with additional data."""
        state_mgr.set_state(123, State.WAITING_INPUT, field="value")
        data = state_mgr.get_data(123)
        assert data["field"] == "value"

    def test_update_data(self, state_mgr: StateManager) -> None:
        """Test updating state data."""
        state_mgr.set_state(123, State.WAITING_INPUT)
        state_mgr.update_data(123, key1="val1", key2="val2")

        data = state_mgr.get_data(123)
        assert data["key1"] == "val1"
        assert data["key2"] == "val2"

    def test_clear_state(self, state_mgr: StateManager) -> None:
        """Test clearing state."""
        state_mgr.set_state(123, State.WAITING_INPUT)
        state_mgr.clear_state(123)

        # Should return NONE for cleared user
        state = state_mgr.get_state(123)
        assert state == State.NONE

    def test_go_back(self, state_mgr: StateManager) -> None:
        """Test going back to previous state."""
        state_mgr.set_state(123, State.WAITING_INPUT)
        state_mgr.set_state(123, State.CONFIRMING)

        previous = state_mgr.go_back(123)
        assert previous == State.WAITING_INPUT

    def test_go_back_to_none(self, state_mgr: StateManager) -> None:
        """Test going back when no history."""
        previous = state_mgr.go_back(123)
        assert previous == State.NONE

    def test_is_in_state(self, state_mgr: StateManager) -> None:
        """Test checking state."""
        state_mgr.set_state(123, State.WAITING_INPUT)

        assert state_mgr.is_in_state(123, State.WAITING_INPUT) is True
        assert state_mgr.is_in_state(123, State.CONFIRMING) is False

    def test_get_data_empty(self, state_mgr: StateManager) -> None:
        """Test getting data for unknown user."""
        data = state_mgr.get_data(999)
        assert data == {}
