from django.db import models, transaction
from django.conf import settings


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
    season = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.season} ({'Open' if self.is_active else 'Closed'})"

class TransferRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CURRENT_CAPTAIN_APPROVED', 'Current Captain Approved'),
        ('NEW_CAPTAIN_APPROVED', 'New Captain Approved'),
        ('ADMIN_APPROVED', 'Admin Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    from_team = models.ForeignKey(Team, related_name='outgoing_transfers', on_delete=models.CASCADE)
    to_team = models.ForeignKey(Team, related_name='incoming_transfers', on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Agreed transfer fee")

    current_captain_approved = models.BooleanField(default=False)
    new_captain_approved = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.name}: {self.from_team.name} -> {self.to_team.name}"

class TransferHistory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    from_team = models.ForeignKey(Team, related_name='history_from', on_delete=models.CASCADE)
    to_team = models.ForeignKey(Team, related_name='history_to', on_delete=models.CASCADE)
    transfer_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.name} to {self.to_team.name} on {self.transfer_date}"
