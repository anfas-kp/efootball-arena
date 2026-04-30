from django import forms
from .models import Team, Player


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo', 'captain_phone', 'platform', 'game', 'description', 'discord', 'instagram']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Team name'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'captain_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'game': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell us about your team...'}),
            'discord': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Discord server link'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@handle'}),
        }


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name', 'photo', 'gaming_id', 'jersey_number', 'position', 'date_of_birth']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Player name'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'gaming_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PSN ID / Gamertag'}),
            'jersey_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '#', 'min': 1, 'max': 99}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
