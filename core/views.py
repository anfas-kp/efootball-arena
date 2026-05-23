from django.shortcuts import render
from tournaments.models import Tournament
from teams.models import Team, TransferHistory
from matches.models import MatchResult


def home(request):
    """Landing page."""
    active_tournaments = Tournament.objects.filter(status__in=['ongoing', 'registration']).order_by('-created_at')[:6]
    total_teams = Team.objects.filter(status='approved').count()
    total_tournaments = Tournament.objects.exclude(status='draft').count()

    # --- Live Feed Activity ---
    recent_matches = MatchResult.objects.filter(status='approved').select_related(
        'fixture__home_team', 'fixture__away_team', 'fixture__league__tournament'
    ).order_by('-verified_at')[:5]
    recent_transfers = TransferHistory.objects.select_related(
        'player', 'from_team', 'to_team'
    ).order_by('-transfer_date')[:5]
    recent_teams = Team.objects.filter(status='approved').order_by('-created_at')[:5]

    feed_items = []
    for match in recent_matches:
        feed_items.append({
            'type': 'match',
            'timestamp': match.verified_at or match.submitted_at,
            'item': match
        })
    for transfer in recent_transfers:
        feed_items.append({
            'type': 'transfer',
            'timestamp': transfer.transfer_date,
            'item': transfer
        })
    for team in recent_teams:
        feed_items.append({
            'type': 'team',
            'timestamp': team.created_at,
            'item': team
        })

    feed_items.sort(key=lambda x: x['timestamp'], reverse=True)
    feed_items = feed_items[:8]  # Show top 8 recent events

    context = {
        'active_tournaments': active_tournaments,
        'total_teams': total_teams,
        'total_tournaments': total_tournaments,
        'feed_items': feed_items,
    }
    return render(request, 'core/home.html', context)
