from celery import shared_task
from django.db.models import Avg, Count, Q
from .models import Player
from matches.models import MatchResult, Goal, Card, PlayerRating, CleanSheet

@shared_task
def repair_all_stats_task():
    """Optimized background task to recalculate all player stats using bulk updates."""
    players = list(Player.objects.all())
    
    # Pre-fetch all approved match results to avoid repetitive DB hits
    approved_results = MatchResult.objects.filter(status='approved').values_list('id', flat=True)
    approved_set = set(approved_results)

    for p in players:
        # Recalculate everything from scratch
        # Use existing relationships but filter by approved status
        p.total_goals = p.goals_scored.filter(result_id__in=approved_set).count()
        p.total_assists = p.assists.filter(result_id__in=approved_set).count()
        p.total_red_cards = p.cards.filter(card_type='red', result_id__in=approved_set).count()
        p.total_yellow_cards = p.cards.filter(card_type='yellow', result_id__in=approved_set).count()
        p.total_clean_sheets = p.clean_sheet_records.filter(result_id__in=approved_set).count()
        
        # Rating (Avoid complex aggregation in loop if possible, but this is okay for small sets)
        ratings = p.match_ratings.filter(result_id__in=approved_set).values_list('rating', flat=True)
        if ratings:
            p.avg_rating = sum(ratings) / len(ratings)
            p.total_rating = sum(ratings)
        else:
            p.avg_rating = 0
            p.total_rating = 0

        # Matches Played (Based on involvement)
        played_ids = set()
        played_ids.update(p.goals_scored.filter(result_id__in=approved_set).values_list('result_id', flat=True))
        played_ids.update(p.assists.filter(result_id__in=approved_set).values_list('result_id', flat=True))
        played_ids.update(p.cards.filter(result_id__in=approved_set).values_list('result_id', flat=True))
        played_ids.update(p.match_ratings.filter(result_id__in=approved_set).values_list('result_id', flat=True))
        played_ids.update(p.clean_sheet_records.filter(result_id__in=approved_set).values_list('result_id', flat=True))
        p.matches_played = len(played_ids)

    # Single bulk update is MUCH faster and won't time out the worker
    Player.objects.bulk_update(players, [
        'total_goals', 'total_assists', 'total_red_cards', 
        'total_yellow_cards', 'total_clean_sheets', 'avg_rating', 
        'total_rating', 'matches_played'
    ])
    
    return "Stats repaired successfully"
