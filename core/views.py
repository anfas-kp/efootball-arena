from django.shortcuts import render
from tournaments.models import Tournament
from teams.models import Team


def home(request):
    """Landing page."""
    active_tournaments = Tournament.objects.filter(status__in=['ongoing', 'registration']).order_by('-created_at')[:6]
    total_teams = Team.objects.filter(status='approved').count()
    total_tournaments = Tournament.objects.exclude(status='draft').count()

    context = {
        'active_tournaments': active_tournaments,
        'total_teams': total_teams,
        'total_tournaments': total_tournaments,
    }
    return render(request, 'core/home.html', context)
