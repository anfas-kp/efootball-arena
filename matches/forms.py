from django import forms
from .models import MatchResult, Goal, Card, PlayerRating
from teams.models import Player


class MatchResultForm(forms.ModelForm):
    class Meta:
        model = MatchResult
        fields = ['home_score', 'away_score', 'screenshot']
        widgets = {
            'home_score': forms.NumberInput(attrs={'class': 'form-control score-input', 'min': 0}),
            'away_score': forms.NumberInput(attrs={'class': 'form-control score-input', 'min': 0}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, is_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = is_admin
        if is_admin:
            self.fields['screenshot'].required = False
            self.fields['screenshot'].help_text = 'Optional for admin'
        else:
            self.fields['screenshot'].required = True
            self.fields['screenshot'].help_text = 'Upload a clear screenshot showing the final score (required)'


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['scorer', 'assist', 'minute', 'goal_type', 'screenshot']
        widgets = {
            'scorer': forms.Select(attrs={'class': 'form-select'}),
            'assist': forms.Select(attrs={'class': 'form-select'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, fixture=None, is_admin=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = is_admin
        if fixture:
            players = Player.objects.filter(team__in=[fixture.home_team, fixture.away_team], is_active=True).order_by('team__name', 'name')
            self.fields['scorer'].queryset = players
            self.fields['scorer'].label_from_instance = lambda obj: f"{obj.name} ({obj.team.name})"
            self.fields['assist'].queryset = players
            self.fields['assist'].label_from_instance = lambda obj: f"{obj.name} ({obj.team.name})"
            self.fields['assist'].required = False
        # Screenshot always optional for goals (was already blank=True on model)
        self.fields['screenshot'].required = False


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute', 'screenshot']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'card_type': forms.Select(attrs={'class': 'form-select'}),
            'minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, fixture=None, is_admin=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = is_admin
        if fixture:
            players = Player.objects.filter(team__in=[fixture.home_team, fixture.away_team], is_active=True).order_by('team__name', 'name')
            self.fields['player'].queryset = players
            self.fields['player'].label_from_instance = lambda obj: f"{obj.name} ({obj.team.name})"
        # Screenshot always optional for cards (was already blank=True on model)
        self.fields['screenshot'].required = False


class PlayerRatingForm(forms.ModelForm):
    class Meta:
        model = PlayerRating
        fields = ['player', 'rating', 'screenshot']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10, 'step': '0.1'}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, fixture=None, is_admin=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = is_admin
        if fixture:
            players = Player.objects.filter(team__in=[fixture.home_team, fixture.away_team], is_active=True).order_by('team__name', 'name')
            self.fields['player'].queryset = players
            self.fields['player'].label_from_instance = lambda obj: f"{obj.name} ({obj.team.name})"
        if is_admin:
            self.fields['screenshot'].required = False
            self.fields['screenshot'].help_text = 'Optional for admin'
        else:
            self.fields['screenshot'].required = True
            self.fields['screenshot'].help_text = 'Upload screenshot of in-game rating (required)'
