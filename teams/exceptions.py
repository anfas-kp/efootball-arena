"""
Custom domain exceptions for the transfer system.

These are raised by the rules engine and service layer, then caught
by views to return user-friendly error messages.
"""


class TransferError(Exception):
    """Base exception for all transfer-related domain errors."""
    pass


class TransferWindowClosed(TransferError):
    """Raised when a transfer is attempted outside an open window."""

    def __init__(self, message="Transfer window is currently closed."):
        self.message = message
        super().__init__(self.message)


class InvalidTransferState(TransferError):
    """Raised when an invalid state machine transition is attempted."""

    def __init__(self, current_status, attempted_status):
        self.current_status = current_status
        self.attempted_status = attempted_status
        self.message = (
            f"Invalid state transition: cannot move from "
            f"'{current_status}' to '{attempted_status}'."
        )
        super().__init__(self.message)


class SquadLimitExceeded(TransferError):
    """Raised when the buying team already has the maximum squad size."""

    def __init__(self, team_name, current_count, max_size=30):
        self.message = (
            f"'{team_name}' already has {current_count}/{max_size} players. "
            f"Cannot add more."
        )
        super().__init__(self.message)


class InsufficientBudget(TransferError):
    """Raised when the buying team cannot afford the transfer fee."""

    def __init__(self, team_name, remaining_budget, transfer_fee):
        self.message = (
            f"'{team_name}' has insufficient budget. "
            f"Remaining: ${remaining_budget:,.0f}, Fee: ${transfer_fee:,.0f}."
        )
        super().__init__(self.message)


class DuplicateTransferRequest(TransferError):
    """Raised when an active request already exists for the same player+team."""

    def __init__(self, player_name, team_name):
        self.message = (
            f"An active transfer request for '{player_name}' "
            f"to '{team_name}' already exists."
        )
        super().__init__(self.message)


class PlayerNotEligible(TransferError):
    """Raised when a player cannot be transferred (e.g. banned, not active)."""

    def __init__(self, message="This player is not eligible for transfer."):
        self.message = message
        super().__init__(self.message)


class TransferTypeNotAllowed(TransferError):
    """Raised when the transfer type is not permitted in the current window."""

    def __init__(self, transfer_type, allowed_types):
        self.message = (
            f"Transfer type '{transfer_type}' is not allowed in this window. "
            f"Allowed: {', '.join(allowed_types) if allowed_types else 'none'}."
        )
        super().__init__(self.message)


class WindowTeamLimitExceeded(TransferError):
    """Raised when a team has reached its per-window transfer limit."""

    def __init__(self, team_name, max_transfers):
        self.message = (
            f"'{team_name}' has reached the maximum of "
            f"{max_transfers} transfers in this window."
        )
        super().__init__(self.message)
