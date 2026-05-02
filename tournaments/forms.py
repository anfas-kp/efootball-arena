from django import forms
from .models import Tournament, League, Fixture


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'banner', 'description', 'rules', 'start_date', 'end_date',
            'registration_deadline', 'max_teams', 'entry_fee', 'prize_pool',
            'status', 'is_open', 'points_win', 'points_draw', 'points_loss'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tournament name'}),
            'banner': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registration_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
            'entry_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prize_pool': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ₹10,000'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_open': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'points_win': forms.NumberInput(attrs={'class': 'form-control'}),
            'points_draw': forms.NumberInput(attrs={'class': 'form-control'}),
            'points_loss': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LeagueForm(forms.ModelForm):
    class Meta:
        model = League
        fields = ['name', 'format', 'max_teams']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., League 1, UCL, UEL'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FixtureForm(forms.ModelForm):
    class Meta:
        model = Fixture
        fields = ['home_team', 'away_team', 'matchday', 'match_date', 'status']
        widgets = {
            'home_team': forms.Select(attrs={'class': 'form-select'}),
            'away_team': forms.Select(attrs={'class': 'form-select'}),
            'matchday': forms.NumberInput(attrs={'class': 'form-control'}),
            'match_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, league, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show teams that are in this league
        self.fields['home_team'].queryset = league.teams.all()
        self.fields['away_team'].queryset = league.teams.all()
