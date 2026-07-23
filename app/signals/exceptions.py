"""Signal Engine exceptions."""


class SignalError(Exception):
    """Base exception for Signal Engine."""


class SignalValidationError(SignalError):
    """Raised when signal validation fails."""


class SignalFilterError(SignalError):
    """Raised when signal filtering fails."""


class SignalDuplicateError(SignalError):
    """Raised when a duplicate signal is detected."""


class SignalCooldownError(SignalError):
    """Raised when a signal is on cooldown."""


class SignalNotFoundError(SignalError):
    """Raised when a signal is not found."""


class SignalPreferenceError(SignalError):
    """Raised when user preferences are invalid."""
