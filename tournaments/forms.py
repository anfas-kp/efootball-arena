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
        fields = ['name', 'format', 'knockout_legs', 'away_goals_rule', 'third_place_match', 'max_teams']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., League 1, UCL, UEL'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'knockout_legs': forms.Select(attrs={'class': 'form-select'}),
            'away_goals_rule': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'third_place_match': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'max_teams': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FixtureForm(forms.ModelForm):
    class Meta:
        model = Fixture
        fields = ['home_team', 'away_team', 'matchday', 'round_type', 'bracket_index', 'match_date', 'status']
        widgets = {
            'home_team': forms.Select(attrs={'class': 'form-select'}),
            'away_team': forms.Select(attrs={'class': 'form-select'}),
            'matchday': forms.NumberInput(attrs={'class': 'form-control'}),
            'round_type': forms.Select(attrs={'class': 'form-select'}),
            'bracket_index': forms.NumberInput(attrs={'class': 'form-control'}),
            'match_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, league, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show teams that are in this league
        self.fields['home_team'].queryset = league.teams.all()
        self.fields['away_team'].queryset = league.teams.all()

class KnockoutGenerationForm(forms.Form):
    """Form to select teams for preliminary round manually."""
    preliminary_teams = forms.ModelMultipleChoiceField(
        queryset=None, 
        required=False, 
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Select teams to play in the Preliminary round. Others will receive a BYE to the next round."
    )

    def __init__(self, league, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preliminary_teams'].queryset = league.teams.all()
