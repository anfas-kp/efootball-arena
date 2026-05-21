import io
from celery import shared_task
from PIL import Image
from django.core.files.base import ContentFile
from django.apps import apps

@shared_task(bind=True, max_retries=3)
def optimize_team_logo(self, team_id):
    """Background task to optimize team logo to WebP."""
    Team = apps.get_model('teams', 'Team')
    try:
        team = Team.objects.get(pk=team_id)
        if not team.logo or team.logo.name.lower().endswith('.webp'):
            return "Already optimized or no logo."

        # Open image from storage
        img_data = team.logo.read()
        img = Image.open(io.BytesIO(img_data))

        if img.format != 'WEBP':
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='WebP', quality=85)
            output.seek(0)
            
            filename = team.logo.name.rsplit('.', 1)[0] + '.webp'
            team.logo.save(filename, ContentFile(output.read()), save=False)
            team.save(update_fields=['logo'])
            return f"Logo optimized for team {team.name}"
            
    except Exception as e:
        # Retry on network issues (like 502)
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def optimize_player_photo(self, player_id):
    """Background task to optimize player photo to WebP."""
    Player = apps.get_model('teams', 'Player')
    try:
        player = Player.objects.get(pk=player_id)
        if not player.photo or player.photo.name.lower().endswith('.webp'):
            return "Already optimized or no photo."

        img_data = player.photo.read()
        img = Image.open(io.BytesIO(img_data))

        if img.format != 'WEBP':
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='WebP', quality=85)
            output.seek(0)
            
            filename = player.photo.name.rsplit('.', 1)[0] + '.webp'
            player.photo.save(filename, ContentFile(output.read()), save=False)
            player.save(update_fields=['photo'])
            return f"Photo optimized for player {player.name}"
            
    except Exception as e:
        raise self.retry(exc=e, countdown=60)


# ===== Transfer System Tasks =====

@shared_task
def auto_manage_transfer_windows():
    """Celery Beat task: auto-open/close transfer windows based on dates.

    Schedule this in CELERY_BEAT_SCHEDULE to run every hour or every 5 minutes.

    Logic:
    - If a window is marked is_active=True but current time is outside
      [start_date, end_date], set is_active=False.
    - If a window is marked is_active=False but current time IS within
      [start_date, end_date], set is_active=True.

    This means admins can still manually override via the toggle,
    but this task keeps things in sync with the configured dates.
    """
    from django.utils import timezone

    TransferWindow = apps.get_model('teams', 'TransferWindow')
    now = timezone.now()
    updated = 0

    for window in TransferWindow.objects.all():
        should_be_active = window.start_date <= now <= window.end_date

        if window.is_active and not should_be_active:
            window.is_active = False
            window.save(update_fields=['is_active'])
            updated += 1
        elif not window.is_active and should_be_active:
            window.is_active = True
            window.save(update_fields=['is_active'])
            updated += 1

    return f"Transfer window sync complete. {updated} window(s) updated."


@shared_task
def expire_loans():
    """Celery Beat task: auto-recall players whose loan period has expired.

    Schedule this to run daily.

    Finds all players where is_on_loan=True and loan_expires <= today,
    then calls TransferService.recall_loan() for each.
    """
    from django.utils import timezone
    from .services import TransferService

    Player = apps.get_model('teams', 'Player')
    today = timezone.now().date()

    expired_loans = Player.objects.filter(
        is_on_loan=True,
        loan_expires__lte=today,
    ).select_related('team', 'parent_club')

    recalled = 0
    errors = []
    for player in expired_loans:
        try:
            TransferService.recall_loan(player)
            recalled += 1
        except Exception as e:
            errors.append(f"{player.name}: {str(e)}")

    result = f"Loan expiry check: {recalled} player(s) recalled."
    if errors:
        result += f" Errors: {'; '.join(errors)}"
    return result


@shared_task
def send_transfer_notification(transfer_request_id, event_type):
    """Send a notification for a transfer event.

    Args:
        transfer_request_id: PK of the TransferRequest.
        event_type: 'initiated', 'approved', 'rejected', 'completed'.

    This is a lightweight in-app notification system.
    Can be extended to send emails via Django's send_mail().
    """
    TransferRequest = apps.get_model('teams', 'TransferRequest')

    try:
        tr = TransferRequest.objects.select_related(
            'player', 'from_team', 'to_team', 'requested_by'
        ).get(pk=transfer_request_id)
    except TransferRequest.DoesNotExist:
        return f"TransferRequest {transfer_request_id} not found."

    # Build notification message based on event
    messages_map = {
        'initiated': (
            f"New transfer request: {tr.requested_by.username} wants to sign "
            f"{tr.player.name} from {tr.from_team.name} "
            f"(Fee: ${tr.transfer_fee:,.0f})"
        ),
        'approved': (
            f"Transfer approved: {tr.player.name} from {tr.from_team.name} "
            f"to {tr.to_team.name} has been approved at this stage."
        ),
        'rejected': (
            f"Transfer rejected: The request for {tr.player.name} "
            f"has been rejected. Reason: {tr.rejection_reason or 'No reason given.'}"
        ),
        'completed': (
            f"Transfer completed: {tr.player.name} has officially moved "
            f"from {tr.from_team.name} to {tr.to_team.name}!"
        ),
    }

    message = messages_map.get(event_type, f"Transfer update for {tr.player.name}.")

    # Log the notification (in production, send email or push notification here)
    import logging
    logger = logging.getLogger('teams.transfers')
    logger.info(f"[Transfer Notification] [{event_type.upper()}] {message}")

    return f"Notification sent: [{event_type}] for {tr.player.name}"

