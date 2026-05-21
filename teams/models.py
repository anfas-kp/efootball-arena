from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Team(models.Model):
    """Represents an e-football team."""

    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    PLATFORM_CHOICES = [
        ('ps4', 'PlayStation 4'),
        ('ps5', 'PlayStation 5'),
        ('xbox', 'Xbox'),
        ('pc', 'PC'),
    ]

    GAME_CHOICES = [
        ('fc25', 'EA FC 25'),
        ('fc24', 'EA FC 24'),
        ('efootball', 'eFootball'),
    ]

    name = models.CharField(max_length=50, unique=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    captain = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team'
    )
    captain_phone = models.CharField(max_length=20, blank=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='ps5')
    game = models.CharField(max_length=20, choices=GAME_CHOICES, default='fc25')
    description = models.TextField(max_length=500, blank=True)
    discord = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total budget allocated to the team")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Optimization is now handled in the background via Celery to avoid 502 timeouts
        super().save(*args, **kwargs)
        
        # Only trigger background optimization if logo is new or just uploaded
        if self.logo and not self.logo.name.lower().endswith('.webp'):
            from .tasks import optimize_team_logo
            transaction.on_commit(lambda: optimize_team_logo.delay(self.pk))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def player_count(self):
        return self.players.count()

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_roster_locked(self):
        """Roster is locked once team is accepted into any active tournament."""
        return self.tournament_applications.filter(status='accepted').exists()

    @property
    def total_player_value(self):
        from django.db.models import Sum
        total = self.players.aggregate(total=Sum('value'))['total']
        return total or 0

    @property
    def remaining_budget(self):
        return self.budget - self.total_player_value


class Player(models.Model):
    """Represents a player on a team."""

    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DEF', 'Defender'),
        ('MID', 'Midfielder'),
        ('FWD', 'Forward'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='player_photos/', blank=True, null=True)
    photo_no_bg = models.ImageField(upload_to='player_photos_nobg/', blank=True, null=True)
    gaming_id = models.CharField(max_length=100, unique=True, blank=True, help_text='PSN ID / Xbox Gamertag / Steam ID')
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Market value of the player')
    is_active = models.BooleanField(default=True)

    # Transfer-related fields
    is_transfer_listed = models.BooleanField(default=False, help_text='Player is available on the transfer market')
    parent_club = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='loaned_out_players',
        help_text='Original club if player is currently on loan'
    )
    is_on_loan = models.BooleanField(default=False)
    loan_expires = models.DateField(null=True, blank=True, help_text='Date the loan period ends')

    # Aggregated stats (updated on result approval)
    total_goals = models.PositiveIntegerField(default=0)
    total_assists = models.PositiveIntegerField(default=0)
    total_red_cards = models.PositiveIntegerField(default=0)
    total_yellow_cards = models.PositiveIntegerField(default=0)
    total_clean_sheets = models.PositiveIntegerField(default=0)
    matches_played = models.PositiveIntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_rating = models.DecimalField(max_digits=6, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validate loan-related field consistency."""
        super().clean()
        if self.is_on_loan:
            if not self.parent_club:
                raise ValidationError({'parent_club': 'A loaned player must have a parent club.'})
            if not self.loan_expires:
                raise ValidationError({'loan_expires': 'A loaned player must have a loan expiry date.'})
        if not self.is_on_loan and (self.parent_club or self.loan_expires):
            raise ValidationError('Parent club and loan expiry should only be set for loaned players.')

    class Meta:
        ordering = ['jersey_number', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name})"

    def save(self, *args, **kwargs):
        # Optimization is now handled in the background via Celery to avoid timeouts
        super().save(*args, **kwargs)

        # Only trigger background optimization if photo is new or just uploaded
        if self.photo and not self.photo.name.lower().endswith('.webp'):
            from .tasks import optimize_player_photo
            transaction.on_commit(lambda: optimize_player_photo.delay(self.pk))

        # Handle background removal only if explicitly requested or needed
        # and not yet processed to save blocking time.
        # Skip if we are just updating stats to avoid heavy processing.
        update_fields = kwargs.get('update_fields')
        is_stat_update = update_fields and not any(f in update_fields for f in ['photo', 'photo_no_bg'])
        
        if self.photo and not self.photo_no_bg and not is_stat_update:
            # Background removal is currently disabled to prevent server crashes on low-resource environments.
            # It requires significant CPU/RAM and can cause Worker Timeouts.
            pass
            """
            try:
                import rembg
                from PIL import Image
                import io
                from django.core.files.base import ContentFile

                # Check if we can actually use rembg (onnxruntime check)
                input_image = Image.open(self.photo.path)
                input_image.thumbnail((800, 800)) # Resize for speed

                # Process with rembg
                output_image = rembg.remove(input_image)
                
                img_io = io.BytesIO()
                output_image.save(img_io, format='WebP', quality=85)
                
                filename = f"{self.pk}_nobg.webp"
                self.photo_no_bg.save(filename, ContentFile(img_io.getvalue()), save=False)
                
                super().save(update_fields=['photo_no_bg'])
            except (ImportError, Exception) as e:
                # Log the error but don't crash the worker
                print(f"Background removal skipped or failed: {e}")
            """


class Trophy(models.Model):
    """A digital badge/trophy awarded to a team or player."""
    CATEGORY_CHOICES = [
        ('team', 'Team Trophy'),
        ('player', 'Player Badge'),
    ]
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='fas fa-trophy', help_text="FontAwesome class, e.g. 'fas fa-trophy' or 'fas fa-medal'")
    color = models.CharField(max_length=50, default='#d4af37', help_text="Hex color code, e.g. '#d4af37'")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='trophies')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True, related_name='badges')
    date_awarded = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Trophies'
        ordering = ['-date_awarded']
        
    def __str__(self):
        if self.category == 'team' and self.team:
            return f"{self.name} - {self.team.name}"
        elif self.category == 'player' and self.player:
            return f"{self.name} - {self.player.name}"
        return self.name

class TransferWindow(models.Model):
    """Manages transfer window periods with configurable rules.
    
    A transfer window defines when player transfers can occur,
    what types are allowed, and per-team limits.
    """

    season = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(
        default=False,
        help_text='Manual override. Window is only open if active AND within date range.'
    )
    allowed_types = models.JSONField(
        default=list,
        blank=True,
        help_text='List of allowed transfer types, e.g. ["permanent", "loan", "free_agent"]. Empty = all allowed.'
    )
    max_transfers_per_team = models.PositiveIntegerField(
        default=5,
        help_text='Maximum transfers a single team can make in this window.'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = 'Open' if self.is_open else 'Closed'
        return f"{self.season} ({status})"

    @property
    def is_open(self):
        """True if manually active AND current time is within the date range."""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def time_remaining(self):
        """Returns timedelta until window closes, or None if closed."""
        if not self.is_open:
            return None
        return self.end_date - timezone.now()

    def clean(self):
        """Validate date ordering."""
        super().clean()
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})


class TransferRequest(models.Model):
    """Core transfer request with strict state machine.
    
    State Machine:
        PENDING -> SELLING_APPROVED -> ADMIN_REVIEW -> COMPLETED
                                                   -> REJECTED
                -> REJECTED
                -> CANCELLED
    """

    TRANSFER_TYPES = [
        ('permanent', 'Permanent Transfer'),
        ('loan', 'Loan'),
        ('free_agent', 'Free Agent'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Selling Club Approval'),
        ('SELLING_APPROVED', 'Selling Club Approved'),
        ('ADMIN_REVIEW', 'Awaiting Admin Review'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Strict state transition map
    VALID_TRANSITIONS = {
        'PENDING': ['SELLING_APPROVED', 'REJECTED', 'CANCELLED'],
        'SELLING_APPROVED': ['ADMIN_REVIEW', 'REJECTED', 'CANCELLED'],
        'ADMIN_REVIEW': ['COMPLETED', 'REJECTED'],
    }

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='transfer_requests')
    from_team = models.ForeignKey(Team, related_name='outgoing_transfers', on_delete=models.CASCADE)
    to_team = models.ForeignKey(Team, related_name='incoming_transfers', on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    window = models.ForeignKey(
        'TransferWindow', on_delete=models.CASCADE,
        related_name='requests', null=True, blank=True
    )

    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='permanent')
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Agreed transfer fee')
    loan_end_date = models.DateField(null=True, blank=True, help_text='Required for loan transfers')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_transfer_type_display()}] {self.player.name}: {self.from_team.name} -> {self.to_team.name}"

    def clean(self):
        """Validate transfer request field consistency."""
        super().clean()
        if self.transfer_type == 'loan' and not self.loan_end_date:
            raise ValidationError({'loan_end_date': 'Loan transfers must have an end date.'})
        if self.from_team_id and self.to_team_id and self.from_team_id == self.to_team_id:
            raise ValidationError('Cannot transfer a player to the same team.')

    def can_transition_to(self, new_status):
        """Check if transitioning from current status to new_status is valid."""
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        return new_status in allowed


class PlayerRegistration(models.Model):
    """Tracks player tournament eligibility per league.
    
    When a player transfers mid-season, the old registration is deactivated
    and a new one is created for the new team.
    """

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='registrations')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='player_registrations')
    league = models.ForeignKey(
        'tournaments.League', on_delete=models.CASCADE,
        related_name='player_registrations'
    )
    eligible_from = models.DateField(help_text='Date from which the player is eligible to play')
    is_active = models.BooleanField(default=True)
    matches_played = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'league', 'team']
        ordering = ['-created_at']

    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f"{self.player.name} @ {self.team.name} in {self.league.name} ({status})"


class TransferHistory(models.Model):
    """Immutable audit log of completed transfers."""

    TRANSFER_TYPES = TransferRequest.TRANSFER_TYPES

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='transfer_history')
    from_team = models.ForeignKey(Team, related_name='history_from', on_delete=models.CASCADE)
    to_team = models.ForeignKey(Team, related_name='history_to', on_delete=models.CASCADE)
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='permanent')
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    window = models.ForeignKey(
        TransferWindow, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='history_entries'
    )
    notes = models.TextField(blank=True)
    transfer_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Transfer histories'
        ordering = ['-transfer_date']

    def __str__(self):
        return f"[{self.get_transfer_type_display()}] {self.player.name} -> {self.to_team.name} ({self.transfer_date:%Y-%m-%d})"
