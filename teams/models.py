from django.db import models
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    is_active = models.BooleanField(default=True)
    # Aggregated stats (updated on result approval)
    total_goals = models.PositiveIntegerField(default=0)
    total_assists = models.PositiveIntegerField(default=0)
    total_red_cards = models.PositiveIntegerField(default=0)
    total_yellow_cards = models.PositiveIntegerField(default=0)
    total_clean_sheets = models.PositiveIntegerField(default=0)
    matches_played = models.PositiveIntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['jersey_number', 'name']

    def __str__(self):
        return f"{self.name} ({self.team.name})"

    def save(self, *args, **kwargs):
        # Handle background removal if photo is uploaded and photo_no_bg is empty
        super().save(*args, **kwargs)
        if self.photo and not self.photo_no_bg:
            try:
                import rembg
                from PIL import Image
                import io
                from django.core.files.base import ContentFile

                input_image = Image.open(self.photo.path)
                
                # Resize if too large to save memory
                input_image.thumbnail((800, 800))

                # Process with rembg
                output_image = rembg.remove(input_image)
                
                # Save to a BytesIO object
                img_io = io.BytesIO()
                output_image.save(img_io, format='PNG')
                
                # Create a Django ContentFile
                filename = f"{self.pk}_nobg.png"
                self.photo_no_bg.save(filename, ContentFile(img_io.getvalue()), save=False)
                
                # Save again to update the photo_no_bg field
                super().save(update_fields=['photo_no_bg'])
            except ImportError:
                print("WARNING: 'rembg' or 'Pillow' is not installed. Background removal skipped. Please run: pip install rembg Pillow")
            except Exception as e:
                print(f"Error removing background: {e}")
