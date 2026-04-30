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

    def __init__(self, team=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if team:
            players = Player.objects.filter(team=team, is_active=True)
            self.fields['scorer'].queryset = players
            self.fields['assist'].queryset = players
            self.fields['assist'].required = False


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

    def __init__(self, team=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if team:
            self.fields['player'].queryset = Player.objects.filter(team=team, is_active=True)


class PlayerRatingForm(forms.ModelForm):
    class Meta:
        model = PlayerRating
        fields = ['player', 'rating', 'screenshot']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10, 'step': '0.1'}),
            'screenshot': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, team=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if team:
            self.fields['player'].queryset = Player.objects.filter(team=team, is_active=True)
