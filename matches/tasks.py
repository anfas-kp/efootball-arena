from celery import shared_task
from django.db.models import Q, Avg
from accounts.models import User
from teams.models import Player, Team
from .models import MatchResult

@shared_task
def sync_match_stats_task(result_id):
    """
    Comprehensive background task to sync all stats related to a match result.
    Recalculates player stats, matches played, and clean sheets.
    """
    try:
        result = MatchResult.objects.get(pk=result_id)
        if result.status != 'approved':
            return "Result not approved, skipping sync."
            
        fixture = result.fixture
        
        # 1. Sync matches_played for both teams
        _sync_player_matches_played(fixture.home_team)
        _sync_player_matches_played(fixture.away_team)
        
        # 2. Identify all unique players involved
        player_ids = set()
        player_ids.update(result.goals.values_list('scorer_id', flat=True))
        player_ids.update(result.goals.exclude(assist=None).values_list('assist_id', flat=True))
        player_ids.update(result.cards.values_list('player_id', flat=True))
        player_ids.update(result.ratings.values_list('player_id', flat=True))
        player_ids.update(result.clean_sheets.values_list('player_id', flat=True))
        
        if player_ids:
            players = Player.objects.filter(id__in=player_ids)
            for player in players:
                player.total_goals = player.goals_scored.filter(result__status='approved').count()
                player.total_assists = player.assists.filter(result__status='approved').count()
                player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
                player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()
                player.total_clean_sheets = player.clean_sheet_records.filter(result__status='approved').count()
                
                ratings = player.match_ratings.filter(result__status='approved')
                player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
                from django.db.models import Sum
                player.total_rating = ratings.aggregate(total=Sum('rating'))['total'] or 0
                
            Player.objects.bulk_update(players, [
                'total_goals', 'total_assists', 'total_red_cards', 
                'total_yellow_cards', 'total_clean_sheets', 'avg_rating', 'total_rating'
            ])
            
        # 3. Sync clean sheet records explicitly
        for cs in result.clean_sheets.all():
            player = cs.player
            player.total_clean_sheets = player.clean_sheet_records.filter(result__status='approved').count()
            player.save(update_fields=['total_clean_sheets'])
            
        return f"Successfully synced stats for {result}"
    except MatchResult.DoesNotExist:
        return "MatchResult not found"

def _sync_player_matches_played(team):
    """Internal helper to update matches_played for a team."""
    match_count = MatchResult.objects.filter(
        Q(fixture__home_team=team) | Q(fixture__away_team=team),
        status='approved'
    ).count()
    team.players.all().update(matches_played=match_count)
