from django.contrib import admin
from .models import MatchResult, Goal, Card, PlayerRating


class GoalInline(admin.TabularInline):
    model = Goal
    extra = 0


class CardInline(admin.TabularInline):
    model = Card
    extra = 0


class PlayerRatingInline(admin.TabularInline):
    model = PlayerRating
    extra = 0


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ('fixture', 'home_score', 'away_score', 'status', 'submitted_at')
    list_filter = ('status',)
    inlines = [GoalInline, CardInline, PlayerRatingInline]
    actions = ['approve_results']

    @admin.action(description='Approve selected results')
    def approve_results(self, request, queryset):
        from django.utils import timezone
        for result in queryset:
            result.status = 'approved'
            result.verified_at = timezone.now()
            result.fixture.status = 'completed'
            result.fixture.save()
            result.save()
            _update_player_stats(result)


def _update_player_stats(result):
    """Recalculate player stats after result approval."""
    from django.db.models import Avg
    # Update goal stats
    for goal in result.goals.all():
        scorer = goal.scorer
        scorer.total_goals = scorer.goals_scored.filter(result__status='approved').count()
        scorer.save(update_fields=['total_goals'])
        if goal.assist:
            assister = goal.assist
            assister.total_assists = assister.assists.filter(result__status='approved').count()
            assister.save(update_fields=['total_assists'])
    # Update card stats
    for card in result.cards.all():
        player = card.player
        player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
        player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()
        player.save(update_fields=['total_red_cards', 'total_yellow_cards'])
    # Update rating stats
    for pr in result.ratings.all():
        player = pr.player
        ratings = player.match_ratings.filter(result__status='approved')
        player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
        player.save(update_fields=['avg_rating'])
