import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from django.http import HttpResponse
from tournaments.models import Fixture
from teams.models import Player
from .models import MatchResult, Goal, Card, PlayerRating
from .forms import MatchResultForm, GoalForm, CardForm, PlayerRatingForm


@login_required
def submit_result(request, fixture_pk):
    """Submit a match result with screenshot proof."""
    fixture = get_object_or_404(Fixture, pk=fixture_pk)

    # Check if user's team is in this fixture
    user_team = getattr(request.user, 'team', None)
    if not user_team or (user_team != fixture.home_team and user_team != fixture.away_team):
        if not request.user.is_admin_user:
            messages.error(request, 'You are not part of this fixture.')
            return redirect('core:home')

    # Check if result already submitted
    if hasattr(fixture, 'result'):
        messages.info(request, 'Result already submitted for this match.')
        return redirect('matches:result_detail', pk=fixture.result.pk)

    if request.method == 'POST':
        form = MatchResultForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.fixture = fixture
            result.submitted_by = request.user
            result.save()
            fixture.status = 'in_progress'
            fixture.save()
            messages.success(request, '📸 Result submitted! Now add goal details, cards, and top rated players.')
            return redirect('matches:result_detail', pk=result.pk)
    else:
        form = MatchResultForm()

    return render(request, 'matches/submit_result.html', {
        'form': form,
        'fixture': fixture,
    })


@login_required
def add_goal(request, result_pk):
    """Add goal details to a match result."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    if not user_team or (user_team != fixture.home_team and user_team != fixture.away_team):
        if not request.user.is_admin_user:
            messages.error(request, 'Access denied.')
            return redirect('core:home')

    # Determine which team to add goal for
    team = user_team if user_team else fixture.home_team

    if request.method == 'POST':
        scoring_team_id = request.POST.get('scoring_team')
        if scoring_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=scoring_team_id)

        form = GoalForm(team=team, data=request.POST, files=request.FILES)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.result = result
            goal.team = team
            goal.save()
            messages.success(request, f'⚽ Goal by {goal.scorer.name} added!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = GoalForm(team=team)

    return render(request, 'matches/add_goal.html', {
        'form': form,
        'result': result,
        'fixture': fixture,
        'home_team': fixture.home_team,
        'away_team': fixture.away_team,
    })


@login_required
def add_card(request, result_pk):
    """Add a disciplinary card to a match result."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    if not user_team or (user_team != fixture.home_team and user_team != fixture.away_team):
        if not request.user.is_admin_user:
            messages.error(request, 'Access denied.')
            return redirect('core:home')

    team = user_team if user_team else fixture.home_team

    if request.method == 'POST':
        card_team_id = request.POST.get('card_team')
        if card_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=card_team_id)

        form = CardForm(team=team, data=request.POST, files=request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.result = result
            card.team = team
            card.save()
            emoji = '🟨' if card.card_type == 'yellow' else '🟥'
            messages.success(request, f'{emoji} {card.get_card_type_display()} for {card.player.name} added!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = CardForm(team=team)

    return render(request, 'matches/add_card.html', {
        'form': form, 'result': result, 'fixture': fixture,
        'home_team': fixture.home_team, 'away_team': fixture.away_team,
    })


@login_required
def add_rating(request, result_pk):
    """Add a top-rated player entry for a match result."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    if not user_team or (user_team != fixture.home_team and user_team != fixture.away_team):
        if not request.user.is_admin_user:
            messages.error(request, 'Access denied.')
            return redirect('core:home')

    team = user_team if user_team else fixture.home_team

    # Check if team already has 3 ratings for this match
    existing_count = result.ratings.filter(team=team).count()
    if existing_count >= 3:
        messages.warning(request, 'You already submitted 3 top-rated players for this match.')
        return redirect('matches:result_detail', pk=result_pk)

    if request.method == 'POST':
        rating_team_id = request.POST.get('rating_team')
        if rating_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=rating_team_id)

        form = PlayerRatingForm(team=team, data=request.POST, files=request.FILES)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.result = result
            rating.team = team
            rating.save()
            messages.success(request, f'⭐ {rating.player.name} rated {rating.rating}/10!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = PlayerRatingForm(team=team)

    return render(request, 'matches/add_rating.html', {
        'form': form, 'result': result, 'fixture': fixture,
        'home_team': fixture.home_team, 'away_team': fixture.away_team,
        'existing_count': existing_count,
    })


def result_detail(request, pk):
    """View match result details."""
    result = get_object_or_404(MatchResult, pk=pk)
    goals = result.goals.all()
    cards = result.cards.all()
    ratings = result.ratings.all()
    return render(request, 'matches/result_detail.html', {
        'result': result,
        'goals': goals,
        'cards': cards,
        'ratings': ratings,
    })


def result_list(request):
    """List all approved results."""
    results = MatchResult.objects.filter(status='approved')
    return render(request, 'matches/result_list.html', {'results': results})


# ===== Leaderboards =====

def leaderboard(request):
    """Public leaderboard — top scorers, assists, ratings."""
    top_scorers = Player.objects.filter(total_goals__gt=0).order_by('-total_goals')[:20]
    top_assists = Player.objects.filter(total_assists__gt=0).order_by('-total_assists')[:20]
    top_rated = Player.objects.filter(avg_rating__gt=0).order_by('-avg_rating')[:20]
    most_cards = Player.objects.filter(
        Q(total_red_cards__gt=0) | Q(total_yellow_cards__gt=0)
    ).order_by('-total_red_cards', '-total_yellow_cards')[:20]

    return render(request, 'matches/leaderboard.html', {
        'top_scorers': top_scorers,
        'top_assists': top_assists,
        'top_rated': top_rated,
        'most_cards': most_cards,
    })


@login_required
def download_top_scorers_pdf(request):
    """Download top scorers as PDF (Admin only)."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    top_scorers = Player.objects.filter(total_goals__gt=0).order_by('-total_goals')

    return render(request, 'matches/pdf_top_scorers.html', {
        'top_scorers': top_scorers
    })


# ===== Admin Views =====

def _sync_player_stats(result):
    """Recalculate player stats after result approval."""
    for goal in result.goals.all():
        scorer = goal.scorer
        scorer.total_goals = scorer.goals_scored.filter(result__status='approved').count()
        scorer.save(update_fields=['total_goals'])
        if goal.assist:
            assister = goal.assist
            assister.total_assists = assister.assists.filter(result__status='approved').count()
            assister.save(update_fields=['total_assists'])
    for card in result.cards.all():
        player = card.player
        player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
        player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()
        player.save(update_fields=['total_red_cards', 'total_yellow_cards'])
    for pr in result.ratings.all():
        player = pr.player
        ratings = player.match_ratings.filter(result__status='approved')
        player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
        player.save(update_fields=['avg_rating'])


@login_required
def admin_verify_results(request):
    """Admin view pending results."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    status_filter = request.GET.get('status', 'pending')
    results = MatchResult.objects.all()
    if status_filter != 'all':
        results = results.filter(status=status_filter)

    return render(request, 'matches/admin_verify.html', {
        'results': results, 'status_filter': status_filter
    })


@login_required
def admin_approve_result(request, pk):
    """Approve a match result and sync player stats."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    result = get_object_or_404(MatchResult, pk=pk)
    result.status = 'approved'
    result.verified_at = timezone.now()
    result.save()

    fixture = result.fixture
    fixture.status = 'completed'
    fixture.save()

    # Sync player stats
    _sync_player_stats(result)

    messages.success(request, f'✅ Result approved: {result}')
    return redirect('matches:admin_verify')


@login_required
def admin_reject_result(request, pk):
    """Reject a match result."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    result = get_object_or_404(MatchResult, pk=pk)
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        result.status = 'rejected'
        result.admin_notes = notes
        result.save()
        messages.success(request, f'❌ Result rejected.')
    return redirect('matches:admin_verify')
