from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Goal, Card, PlayerRating, CleanSheet


@receiver(post_delete, sender=Goal)
def recalc_on_goal_delete(sender, instance, **kwargs):
    """When a goal is deleted (directly or via cascade), recalculate player stats."""
    try:
        scorer = instance.scorer
        scorer.total_goals = scorer.goals_scored.filter(result__status='approved').count()
        scorer.save(update_fields=['total_goals'])
    except Exception:
        pass

    try:
        if instance.assist:
            assister = instance.assist
            assister.total_assists = assister.assists.filter(result__status='approved').count()
            assister.save(update_fields=['total_assists'])
    except Exception:
        pass


@receiver(post_delete, sender=Card)
def recalc_on_card_delete(sender, instance, **kwargs):
    """When a card is deleted (directly or via cascade), recalculate player stats."""
    try:
        player = instance.player
        player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
        player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()
        player.save(update_fields=['total_red_cards', 'total_yellow_cards'])
    except Exception:
        pass


@receiver(post_delete, sender=PlayerRating)
def recalc_on_rating_delete(sender, instance, **kwargs):
    """When a rating is deleted (directly or via cascade), recalculate player stats."""
    try:
        player = instance.player
        ratings = player.match_ratings.filter(result__status='approved')
        player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
        player.save(update_fields=['avg_rating'])
    except Exception:
        pass


@receiver(post_delete, sender=CleanSheet)
def recalc_on_clean_sheet_delete(sender, instance, **kwargs):
    """When a clean sheet is deleted (directly or via cascade), recalculate player stats."""
    try:
        player = instance.player
        player.total_clean_sheets = player.clean_sheet_records.filter(
            result__status='approved'
        ).count()
        player.save(update_fields=['total_clean_sheets'])
    except Exception:
        pass
