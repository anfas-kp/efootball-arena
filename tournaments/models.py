from django.db import models
from django.utils import timezone
from teams.models import Team


class Tournament(models.Model):
    """Represents a tournament container."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('registration', 'Registration Open'),
        ('closed', 'Registration Closed'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    banner = models.ImageField(upload_to='tournament_banners/', blank=True, null=True)
    description = models.TextField(blank=True)
    rules = models.TextField(blank=True, help_text='Tournament rules and regulations')
    start_date = models.DateField()
    end_date = models.DateField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    max_teams = models.PositiveIntegerField(default=16)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prize_pool = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_open = models.BooleanField(default=False, help_text='Allow teams to self-apply for this tournament')
    points_win = models.PositiveIntegerField(default=3)
    points_draw = models.PositiveIntegerField(default=1)
    points_loss = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def entry_gate_closed(self):
        """Check if the registration window has passed."""
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return True
        return False

    @property
    def is_tournament_full(self):
        """Check if accepted teams have reached max_teams limit."""
        accepted_count = self.applications.filter(status='accepted').count()
        return accepted_count >= self.max_teams

    @property
    def accepted_team_count(self):
        return self.applications.filter(status='accepted').count()

    @property
    def can_accept_applications(self):
        return not self.entry_gate_closed and not self.is_tournament_full


class TournamentApplication(models.Model):
    """A team's application to join a tournament."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name='applications'
    )
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='tournament_applications'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_league = models.ForeignKey(
        'League', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='applications', help_text='League assigned upon acceptance'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['tournament', 'team']

    def __str__(self):
        return f"{self.team.name} → {self.tournament.name} [{self.get_status_display()}]"


class League(models.Model):
    """A league/division within a tournament (e.g., League 1, UCL, UEL)."""

    FORMAT_CHOICES = [
        ('round_robin', 'Round Robin (Single Leg)'),
        ('round_robin_2leg', 'Round Robin (2 Legs)'),
        ('group_stage', 'Group Stage'),
        ('knockout', 'Knockout'),
        ('group_knockout', 'Group Stage + Knockout'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='leagues')
    name = models.CharField(max_length=100)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='round_robin')
    max_teams = models.PositiveIntegerField(default=16)
    teams = models.ManyToManyField(Team, blank=True, related_name='leagues')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['tournament', 'name']

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"

    @property
    def team_count(self):
        return self.teams.count()

    @property
    def is_full(self):
        return self.team_count >= self.max_teams


class Fixture(models.Model):
    """A scheduled match between two teams."""

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='fixtures')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_fixtures')
    matchday = models.PositiveIntegerField(default=1)
    match_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['matchday', 'created_at']

    def __str__(self):
        return f"MD{self.matchday}: {self.home_team.name} vs {self.away_team.name}"
