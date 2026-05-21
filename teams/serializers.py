"""
Transfer Serializers (Pure Django — no DRF dependency).

Provides functions to convert model instances to JSON-safe dicts.
Separate "read" serializers (nested, rich) for dashboards
and "write" serializers (flat IDs) for create/update operations.
"""

from decimal import Decimal


def _decimal_to_float(val):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(val, Decimal):
        return float(val)
    return val


# ------------------------------------------------------------------
# Read Serializers (rich, nested — for GET endpoints / dashboards)
# ------------------------------------------------------------------

def serialize_team_brief(team):
    """Minimal team representation for nested embedding."""
    if team is None:
        return None
    return {
        'id': team.pk,
        'name': team.name,
        'logo': team.logo.url if team.logo else None,
        'budget': _decimal_to_float(team.budget),
        'remaining_budget': _decimal_to_float(team.remaining_budget),
        'player_count': team.player_count,
    }


def serialize_player_brief(player):
    """Minimal player representation for nested embedding."""
    if player is None:
        return None
    return {
        'id': player.pk,
        'name': player.name,
        'position': player.position,
        'jersey_number': player.jersey_number,
        'value': _decimal_to_float(player.value),
        'photo': player.photo.url if player.photo else None,
        'team': serialize_team_brief(player.team) if hasattr(player, 'team') and player.team_id else None,
        'is_on_loan': player.is_on_loan,
        'is_transfer_listed': player.is_transfer_listed,
    }


def serialize_transfer_window(window):
    """Full transfer window details including computed properties."""
    if window is None:
        return None

    time_remaining = window.time_remaining
    remaining_seconds = int(time_remaining.total_seconds()) if time_remaining else None

    return {
        'id': window.pk,
        'season': window.season,
        'start_date': window.start_date.isoformat(),
        'end_date': window.end_date.isoformat(),
        'is_active': window.is_active,
        'is_open': window.is_open,
        'time_remaining_seconds': remaining_seconds,
        'allowed_types': window.allowed_types,
        'max_transfers_per_team': window.max_transfers_per_team,
        'notes': window.notes,
    }


def serialize_transfer_request(transfer_request):
    """Rich transfer request with nested player/team data for dashboards."""
    tr = transfer_request
    return {
        'id': tr.pk,
        'player': serialize_player_brief(tr.player),
        'from_team': serialize_team_brief(tr.from_team),
        'to_team': serialize_team_brief(tr.to_team),
        'transfer_type': tr.transfer_type,
        'transfer_type_display': tr.get_transfer_type_display(),
        'transfer_fee': _decimal_to_float(tr.transfer_fee),
        'loan_end_date': tr.loan_end_date.isoformat() if tr.loan_end_date else None,
        'status': tr.status,
        'status_display': tr.get_status_display(),
        'rejection_reason': tr.rejection_reason,
        'requested_by': tr.requested_by.username if tr.requested_by else None,
        'window': serialize_transfer_window(tr.window) if tr.window_id else None,
        'completed_at': tr.completed_at.isoformat() if tr.completed_at else None,
        'created_at': tr.created_at.isoformat(),
        'updated_at': tr.updated_at.isoformat(),
    }


def serialize_transfer_history(history):
    """Audit log entry serializer."""
    h = history
    return {
        'id': h.pk,
        'player': serialize_player_brief(h.player),
        'from_team': serialize_team_brief(h.from_team),
        'to_team': serialize_team_brief(h.to_team),
        'transfer_type': h.transfer_type,
        'transfer_type_display': h.get_transfer_type_display(),
        'transfer_fee': _decimal_to_float(h.transfer_fee),
        'notes': h.notes,
        'transfer_date': h.transfer_date.isoformat(),
    }


# ------------------------------------------------------------------
# Write Helpers (flat — for validating incoming POST payloads)
# ------------------------------------------------------------------

def validate_initiate_payload(data):
    """Validate and extract fields from a transfer initiation request body.

    Args:
        data: dict from request body (parsed JSON or POST data).

    Returns:
        dict with validated fields: player_id, to_team_id, transfer_type, fee, loan_end_date.

    Raises:
        ValueError: If required fields are missing or invalid.
    """
    player_id = data.get('player_id')
    if not player_id:
        raise ValueError("'player_id' is required.")

    transfer_type = data.get('transfer_type', 'permanent')
    if transfer_type not in ('permanent', 'loan', 'free_agent'):
        raise ValueError(f"Invalid transfer type: '{transfer_type}'.")

    fee = data.get('fee', 0)
    try:
        fee = Decimal(str(fee))
    except Exception:
        raise ValueError(f"Invalid fee value: '{fee}'.")

    loan_end_date = data.get('loan_end_date')
    if transfer_type == 'loan' and not loan_end_date:
        raise ValueError("'loan_end_date' is required for loan transfers.")

    if loan_end_date:
        from datetime import datetime
        try:
            loan_end_date = datetime.strptime(str(loan_end_date), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid loan_end_date format: '{loan_end_date}'. Use YYYY-MM-DD.")

    return {
        'player_id': int(player_id),
        'transfer_type': transfer_type,
        'fee': fee,
        'loan_end_date': loan_end_date,
    }
