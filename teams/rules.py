"""
Transfer Rules Engine.

All transfer validation rules live here as static methods.
The service layer calls these before performing any state change.
This keeps business rules separate from data access and presentation.
"""

from .exceptions import (
    TransferWindowClosed,
    SquadLimitExceeded,
    InsufficientBudget,
    DuplicateTransferRequest,
    PlayerNotEligible,
    TransferTypeNotAllowed,
    WindowTeamLimitExceeded,
)


class TransferRules:
    """Static validation rules for the transfer system."""

    MAX_SQUAD_SIZE = 30

    @staticmethod
    def check_window_open(window):
        """Ensure the transfer window is open.

        Args:
            window: TransferWindow instance (or None).

        Raises:
            TransferWindowClosed: If no window or window is not open.
        """
        if window is None:
            raise TransferWindowClosed("No active transfer window exists.")
        if not window.is_open:
            raise TransferWindowClosed(
                f"Transfer window '{window.season}' is currently closed."
            )

    @staticmethod
    def check_squad_limit(team, max_size=None):
        """Ensure the team has room for another player.

        Args:
            team: Team instance (buying team).
            max_size: Override the default squad limit.

        Raises:
            SquadLimitExceeded: If team is at or above the limit.
        """
        limit = max_size or TransferRules.MAX_SQUAD_SIZE
        current_count = team.players.filter(is_active=True).count()
        if current_count >= limit:
            raise SquadLimitExceeded(team.name, current_count, limit)

    @staticmethod
    def check_budget(team, fee):
        """Ensure the buying team can afford the transfer fee.

        Args:
            team: Team instance (buying team).
            fee: Decimal transfer fee.

        Raises:
            InsufficientBudget: If remaining budget < fee.
        """
        from decimal import Decimal
        fee = Decimal(str(fee))
        if fee > 0 and team.remaining_budget < fee:
            raise InsufficientBudget(team.name, team.remaining_budget, fee)

    @staticmethod
    def check_no_duplicate(player, to_team):
        """Ensure no active transfer request exists for this player+team combo.

        Args:
            player: Player instance.
            to_team: Team instance (buying team).

        Raises:
            DuplicateTransferRequest: If an active request already exists.
        """
        from .models import TransferRequest
        active_statuses = ['PENDING', 'SELLING_APPROVED', 'ADMIN_REVIEW']
        if TransferRequest.objects.filter(
            player=player,
            to_team=to_team,
            status__in=active_statuses,
        ).exists():
            raise DuplicateTransferRequest(player.name, to_team.name)

    @staticmethod
    def check_player_eligible(player, to_team):
        """Ensure the player can be transferred.

        Checks:
            - Player is active.
            - Player is not already on the buying team.

        Args:
            player: Player instance.
            to_team: Team instance (buying team).

        Raises:
            PlayerNotEligible: If the player fails eligibility checks.
        """
        if not player.is_active:
            raise PlayerNotEligible(
                f"'{player.name}' is currently inactive and cannot be transferred."
            )
        if player.team_id == to_team.pk:
            raise PlayerNotEligible(
                f"'{player.name}' is already on '{to_team.name}'."
            )

    @staticmethod
    def check_transfer_type_allowed(window, transfer_type):
        """Ensure the transfer type is permitted in this window.

        If window.allowed_types is empty, all types are allowed.

        Args:
            window: TransferWindow instance.
            transfer_type: str ('permanent', 'loan', 'free_agent').

        Raises:
            TransferTypeNotAllowed: If the type is not in the allowed list.
        """
        if window.allowed_types and transfer_type not in window.allowed_types:
            raise TransferTypeNotAllowed(transfer_type, window.allowed_types)

    @staticmethod
    def check_window_team_limit(window, team):
        """Ensure the team hasn't exceeded its per-window transfer limit.

        Counts completed transfers where the team is the buyer.

        Args:
            window: TransferWindow instance.
            team: Team instance (buying team).

        Raises:
            WindowTeamLimitExceeded: If limit is reached.
        """
        from .models import TransferRequest
        completed_count = TransferRequest.objects.filter(
            window=window,
            to_team=team,
            status='COMPLETED',
        ).count()
        if completed_count >= window.max_transfers_per_team:
            raise WindowTeamLimitExceeded(team.name, window.max_transfers_per_team)

    @staticmethod
    def validate_all(player, from_team, to_team, window, transfer_type, fee):
        """Run all validation rules in sequence.

        This is the main entry point called by the service layer.
        Raises the first rule that fails.
        """
        TransferRules.check_window_open(window)
        TransferRules.check_player_eligible(player, to_team)
        TransferRules.check_no_duplicate(player, to_team)
        TransferRules.check_transfer_type_allowed(window, transfer_type)
        TransferRules.check_squad_limit(to_team)
        TransferRules.check_budget(to_team, fee)
        TransferRules.check_window_team_limit(window, to_team)
