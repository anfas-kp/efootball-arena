from django.db import models
from tournaments.models import Fixture
from teams.models import Team, Player


class MatchResult(models.Model):
    """Result of a completed match."""

    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disputed', 'Disputed'),
    ]

    fixture = models.OneToOneField(Fixture, on_delete=models.CASCADE, related_name='result')
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    screenshot = models.ImageField(upload_to='match_screenshots/', blank=True, null=True, help_text='Full-time scoreline screenshot')
    submitted_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='submitted_results'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.fixture.home_team.name} {self.home_score}-{self.away_score} {self.fixture.away_team.name}"

    @property
    def winner(self):
        if self.home_score > self.away_score:
            return self.fixture.home_team
        elif self.away_score > self.home_score:
            return self.fixture.away_team
        return None

    @property
    def is_draw(self):
        return self.home_score == self.away_score


class Goal(models.Model):
    """A goal scored in a match."""

    GOAL_TYPE_CHOICES = [
        ('open_play', 'Open Play'),
        ('penalty', 'Penalty'),
        ('free_kick', 'Free Kick'),
        ('header', 'Header'),
        ('volley', 'Volley'),
        ('own_goal', 'Own Goal'),
    ]

    result = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    scorer = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals_scored')
    assist = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='assists'
    )
    minute = models.PositiveIntegerField(help_text='Minute of the goal')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, default='open_play')
    screenshot = models.ImageField(upload_to='goal_screenshots/', blank=True, null=True)

    class Meta:
        ordering = ['minute']

    def __str__(self):
        return f"⚽ {self.scorer.name} ({self.minute}')"


class Card(models.Model):
    """Disciplinary card in a match."""

    CARD_CHOICES = [
        ('yellow', 'Yellow Card'),
        ('red', 'Red Card'),
    ]

    result = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='cards')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    card_type = models.CharField(max_length=10, choices=CARD_CHOICES)
    minute = models.PositiveIntegerField()
    screenshot = models.ImageField(
        upload_to='card_screenshots/', blank=True, null=True,
        help_text='Screenshot proof (mandatory for red cards)'
    )

    class Meta:
        ordering = ['minute']

    def __str__(self):
        emoji = '🟨' if self.card_type == 'yellow' else '🟥'
        return f"{emoji} {self.player.name} ({self.minute}')"


class PlayerRating(models.Model):
    """Top-rated player entry for a match (each team submits their top 3)."""

    result = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='ratings')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='match_ratings')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1, help_text='Match rating out of 10')
    screenshot = models.ImageField(upload_to='rating_screenshots/', blank=True, null=True, help_text='Screenshot of in-game rating')

    class Meta:
        ordering = ['-rating']
        unique_together = ['result', 'player']

    def __str__(self):
        return f"⭐ {self.player.name} - {self.rating}/10"


class CleanSheet(models.Model):
    """Tracks which GK earned a clean sheet in a match.
    
    Only valid when the GK's team conceded 0 goals.
    One clean sheet entry per team per match.
    """

    result = models.ForeignKey(MatchResult, on_delete=models.CASCADE, related_name='clean_sheets')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='clean_sheet_records')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['result', 'team']  # Max 1 clean sheet per team per match
        ordering = ['team__name']

    def __str__(self):
        return f"🧤 {self.player.name} — Clean Sheet"

