"""
Transfer Service Layer.

All transfer state changes and complex business operations live here.
Views delegate to this layer; they never mutate transfer state directly.
Every write operation is wrapped in transaction.atomic().
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import (
    Player, Team, TransferRequest, TransferHistory,
    TransferWindow, PlayerRegistration,
)
from .rules import TransferRules
from .exceptions import InvalidTransferState, TransferError


class TransferService:
    """Encapsulates all transfer business operations."""

    # ------------------------------------------------------------------
    # Initiate
    # ------------------------------------------------------------------

    @staticmethod
    def initiate_transfer(
        player,
        from_team,
        to_team,
        requested_by,
        window,
        transfer_type='permanent',
        fee=0,
        loan_end_date=None,
    ):
        """Create a new transfer request after validating all rules.

        Args:
            player: Player instance to transfer.
            from_team: Team instance (selling club).
            to_team: Team instance (buying club).
            requested_by: User who initiated the request.
            window: Active TransferWindow instance.
            transfer_type: 'permanent', 'loan', or 'free_agent'.
            fee: Decimal transfer fee.
            loan_end_date: date (required if transfer_type == 'loan').

        Returns:
            TransferRequest: The newly created request.

        Raises:
            TransferError subclass: If any validation rule fails.
        """
        fee = Decimal(str(fee))

        # Run the full rules engine
        TransferRules.validate_all(
            player=player,
            from_team=from_team,
            to_team=to_team,
            window=window,
            transfer_type=transfer_type,
            fee=fee,
        )

        with transaction.atomic():
            transfer_request = TransferRequest.objects.create(
                player=player,
                from_team=from_team,
                to_team=to_team,
                requested_by=requested_by,
                window=window,
                transfer_type=transfer_type,
                transfer_fee=fee,
                loan_end_date=loan_end_date,
                status='PENDING',
            )

        return transfer_request

    # ------------------------------------------------------------------
    # Approval / Rejection
    # ------------------------------------------------------------------

    @staticmethod
    def process_approval(transfer_request, user, action='approve', reason=''):
        """Process an approval or rejection step based on user role.

        The method determines which step to advance based on the
        current status and the user's relationship to the transfer.

        Args:
            transfer_request: TransferRequest instance.
            user: The User performing the action.
            action: 'approve' or 'reject'.
            reason: Rejection reason text (used only on reject).

        Returns:
            str: Description of what happened.

        Raises:
            InvalidTransferState: If the transition is illegal.
            TransferError: If completion rules fail.
        """
        if action == 'reject':
            return TransferService._reject(transfer_request, user, reason)

        if action == 'cancel':
            return TransferService._cancel(transfer_request, user)

        # --- Approve flow ---
        current = transfer_request.status
        user_team = getattr(user, 'team', None)

        # Step 1: Selling club captain approves (PENDING -> SELLING_APPROVED)
        if current == 'PENDING' and user_team and user_team == transfer_request.from_team:
            return TransferService._transition(
                transfer_request, 'SELLING_APPROVED',
                "Selling club approved. Awaiting admin review."
            )

        # Step 2: Admin approves (SELLING_APPROVED -> ADMIN_REVIEW -> COMPLETED)
        if current == 'SELLING_APPROVED' and user.is_admin_user:
            # Move to ADMIN_REVIEW then immediately complete
            TransferService._transition(
                transfer_request, 'ADMIN_REVIEW',
                "Admin reviewing..."
            )
            return TransferService.complete_transfer(transfer_request)

        raise InvalidTransferState(
            current,
            f"approve (by {'admin' if getattr(user, 'is_admin_user', False) else 'captain'})"
        )

    @staticmethod
    def _reject(transfer_request, user, reason=''):
        """Reject a transfer request from any rejectable state."""
        current = transfer_request.status
        if not transfer_request.can_transition_to('REJECTED'):
            raise InvalidTransferState(current, 'REJECTED')

        # Permission check: admin, selling captain, or buying captain
        user_team = getattr(user, 'team', None)
        is_admin = getattr(user, 'is_admin_user', False)
        is_involved = user_team and (
            user_team == transfer_request.from_team or
            user_team == transfer_request.to_team
        )

        if not is_admin and not is_involved:
            raise InvalidTransferState(current, 'REJECTED')

        with transaction.atomic():
            transfer_request.status = 'REJECTED'
            transfer_request.rejection_reason = reason or 'Rejected by user.'
            transfer_request.save(update_fields=['status', 'rejection_reason', 'updated_at'])

        return f"Transfer request for {transfer_request.player.name} rejected."

    @staticmethod
    def _cancel(transfer_request, user):
        """Cancel a transfer request (only by the requesting user/team)."""
        current = transfer_request.status
        if not transfer_request.can_transition_to('CANCELLED'):
            raise InvalidTransferState(current, 'CANCELLED')

        user_team = getattr(user, 'team', None)
        if user_team != transfer_request.to_team and user != transfer_request.requested_by:
            raise InvalidTransferState(current, 'CANCELLED')

        with transaction.atomic():
            transfer_request.status = 'CANCELLED'
            transfer_request.save(update_fields=['status', 'updated_at'])

        return f"Transfer request for {transfer_request.player.name} cancelled."

    @staticmethod
    def _transition(transfer_request, new_status, message):
        """Perform a validated state transition.

        Raises:
            InvalidTransferState: If the transition is not allowed.
        """
        if not transfer_request.can_transition_to(new_status):
            raise InvalidTransferState(transfer_request.status, new_status)

        with transaction.atomic():
            transfer_request.status = new_status
            transfer_request.save(update_fields=['status', 'updated_at'])

        return message

    # ------------------------------------------------------------------
    # Complete Transfer
    # ------------------------------------------------------------------

    @staticmethod
    def complete_transfer(transfer_request):
        """Execute the final atomic transfer: move player, update budgets,
        set loan fields, create history, manage registrations.

        This is the most critical method — everything happens atomically.

        Args:
            transfer_request: TransferRequest in ADMIN_REVIEW status.

        Returns:
            str: Success message.
        """
        with transaction.atomic():
            # Lock the rows we're about to mutate
            tr = TransferRequest.objects.select_for_update().get(
                pk=transfer_request.pk
            )
            buyer = Team.objects.select_for_update().get(pk=tr.to_team_id)
            seller = Team.objects.select_for_update().get(pk=tr.from_team_id)
            player = Player.objects.select_for_update().get(pk=tr.player_id)

            fee = tr.transfer_fee
            old_team = seller

            # 1. Budget transfer
            if fee > 0:
                buyer.budget -= fee
                seller.budget += fee
                buyer.save(update_fields=['budget'])
                seller.save(update_fields=['budget'])

            # 2. Move player
            player.team = buyer

            if tr.transfer_type == 'loan':
                player.is_on_loan = True
                player.parent_club = old_team
                player.loan_expires = tr.loan_end_date
            elif tr.transfer_type == 'permanent':
                # If player was on loan and is now permanently transferred
                player.is_on_loan = False
                player.parent_club = None
                player.loan_expires = None

            player.save(update_fields=[
                'team', 'is_on_loan', 'parent_club', 'loan_expires',
            ])

            # 3. Deactivate old registrations and create new ones
            PlayerRegistration.objects.filter(
                player=player,
                team=old_team,
                is_active=True,
            ).update(is_active=False)

            # Register player for buyer's active leagues
            for league in buyer.leagues.all():
                PlayerRegistration.objects.get_or_create(
                    player=player,
                    league=league,
                    team=buyer,
                    defaults={
                        'eligible_from': timezone.now().date(),
                        'is_active': True,
                    },
                )

            # 4. Create immutable audit log
            TransferHistory.objects.create(
                player=player,
                from_team=seller,
                to_team=buyer,
                transfer_type=tr.transfer_type,
                transfer_fee=fee,
                window=tr.window,
            )

            # 5. Finalize the request
            tr.status = 'COMPLETED'
            tr.completed_at = timezone.now()
            tr.save(update_fields=['status', 'completed_at', 'updated_at'])

        return f"Transfer of {player.name} to {buyer.name} completed successfully."

    # ------------------------------------------------------------------
    # Loan Recall
    # ------------------------------------------------------------------

    @staticmethod
    def recall_loan(player):
        """Recall a player from loan back to their parent club.

        Args:
            player: Player instance currently on loan.

        Returns:
            str: Success message.

        Raises:
            TransferError: If the player is not on loan.
        """
        if not player.is_on_loan or not player.parent_club:
            raise TransferError(
                f"'{player.name}' is not currently on loan."
            )

        with transaction.atomic():
            loan_team = player.team
            parent = player.parent_club

            # Move player back
            player.team = parent
            player.is_on_loan = False
            player.parent_club = None
            player.loan_expires = None
            player.save(update_fields=[
                'team', 'is_on_loan', 'parent_club', 'loan_expires',
            ])

            # Update registrations
            PlayerRegistration.objects.filter(
                player=player,
                team=loan_team,
                is_active=True,
            ).update(is_active=False)

            for league in parent.leagues.all():
                PlayerRegistration.objects.get_or_create(
                    player=player,
                    league=league,
                    team=parent,
                    defaults={
                        'eligible_from': timezone.now().date(),
                        'is_active': True,
                    },
                )

            # Audit log
            TransferHistory.objects.create(
                player=player,
                from_team=loan_team,
                to_team=parent,
                transfer_type='loan',
                transfer_fee=0,
                notes='Loan recall',
            )

        return f"'{player.name}' recalled from loan at '{loan_team.name}' back to '{parent.name}'."
