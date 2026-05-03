import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from django.http import HttpResponse
from tournaments.models import Fixture
from teams.models import Player
from .models import MatchResult, Goal, Card, PlayerRating, CleanSheet
from .forms import MatchResultForm, AdminEditScoreForm, GoalForm, CardForm, PlayerRatingForm, CleanSheetForm


def _recalculate_score(result):
    """Auto-calculate home_score and away_score from goals.
    
    Regular goals count for the scorer's team.
    Own goals count for the OPPOSING team.
    """
    fixture = result.fixture
    home_team = fixture.home_team
    away_team = fixture.away_team

    # Home team score = home team's regular goals + away team's own goals
    home_score = result.goals.filter(
        team=home_team
    ).exclude(goal_type='own_goal').count() + result.goals.filter(
        team=away_team, goal_type='own_goal'
    ).count()

    # Away team score = away team's regular goals + home team's own goals
    away_score = result.goals.filter(
        team=away_team
    ).exclude(goal_type='own_goal').count() + result.goals.filter(
        team=home_team, goal_type='own_goal'
    ).count()

    result.home_score = home_score
    result.away_score = away_score
    result.save(update_fields=['home_score', 'away_score'])


@login_required
def submit_result(request, fixture_pk):
    """Submit a match result. Teams upload screenshot, then add goals.
    Score auto-calculates from goals."""
    fixture = get_object_or_404(Fixture, pk=fixture_pk)

    # Check if user's team is in this fixture
    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    if not is_team_member and not is_admin:
        messages.error(request, 'You are not part of this fixture.')
        return redirect('core:home')

    # Check if result already submitted
    if hasattr(fixture, 'result'):
        messages.info(request, 'Result already submitted for this match.')
        return redirect('matches:result_detail', pk=fixture.result.pk)

    if request.method == 'POST':
        form = MatchResultForm(request.POST, request.FILES, is_admin=is_admin)
        if form.is_valid():
            result = form.save(commit=False)
            result.fixture = fixture
            result.submitted_by = request.user
            result.home_score = 0
            result.away_score = 0
            
            if is_admin:
                result.status = 'approved'
                result.verified_at = timezone.now()
            
            result.save()
            
            if is_admin:
                fixture.status = 'completed'
            else:
                fixture.status = 'in_progress'
            fixture.save()
            
            if is_admin:
                messages.success(request, '✅ Result created and auto-approved! Now add goals — score will be calculated automatically.')
            else:
                messages.success(request, '📸 Result submitted! Now add goals, cards, and top rated players. Score will update automatically.')
            return redirect('matches:result_detail', pk=result.pk)
    else:
        form = MatchResultForm(is_admin=is_admin)

    return render(request, 'matches/submit_result.html', {
        'form': form,
        'fixture': fixture,
        'is_admin': is_admin,
    })


@login_required
def edit_result(request, pk):
    """Edit an existing match result. Admin can manually override score."""
    result = get_object_or_404(MatchResult, pk=pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)
    
    if not is_team_member and not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    # If result is already approved, only admin can edit
    if result.status == 'approved' and not is_admin:
        messages.error(request, 'Approved results can only be edited by an admin.')
        return redirect('matches:result_detail', pk=pk)

    if request.method == 'POST':
        if is_admin:
            form = AdminEditScoreForm(request.POST, request.FILES, instance=result)
        else:
            form = MatchResultForm(request.POST, request.FILES, instance=result)
        
        if form.is_valid():
            updated_result = form.save()
            if is_admin and updated_result.status == 'approved':
                _sync_player_stats(updated_result)
                _sync_clean_sheet_stats(updated_result)
            messages.success(request, 'Result updated!')
            return redirect('matches:result_detail', pk=pk)
    else:
        if is_admin:
            form = AdminEditScoreForm(instance=result)
        else:
            form = MatchResultForm(instance=result)

    return render(request, 'matches/edit_result.html', {
        'form': form,
        'result': result,
        'fixture': fixture,
        'is_admin': is_admin,
    })


@login_required
def add_goal(request, result_pk):
    """Add goal details to a match result. Score auto-recalculates."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    if not is_team_member and not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if not is_admin and result.status == 'approved':
        messages.error(request, 'Cannot modify approved results. Contact admin.')
        return redirect('matches:result_detail', pk=result_pk)

    team = user_team if user_team else fixture.home_team

    if request.method == 'POST':
        scoring_team_id = request.POST.get('scoring_team')
        if scoring_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=scoring_team_id)

        form = GoalForm(fixture=fixture, is_admin=is_admin, data=request.POST, files=request.FILES)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.result = result
            goal.team = goal.scorer.team
            goal.save()

            # Auto-recalculate score from goals
            _recalculate_score(result)

            if result.status == 'approved':
                _sync_player_stats(result)

            messages.success(request, f'⚽ Goal by {goal.scorer.name} added! Score updated to {result.home_score}-{result.away_score}.')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = GoalForm(fixture=fixture, is_admin=is_admin)

    players_dict = {p.id: p.team_id for p in Player.objects.filter(team__in=[fixture.home_team, fixture.away_team])}

    return render(request, 'matches/add_goal.html', {
        'form': form,
        'result': result,
        'fixture': fixture,
        'home_team': fixture.home_team,
        'away_team': fixture.away_team,
        'players_dict': players_dict,
        'is_admin': is_admin,
    })


@login_required
def add_card(request, result_pk):
    """Add a disciplinary card to a match result."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    if not is_team_member and not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if not is_admin and result.status == 'approved':
        messages.error(request, 'Cannot modify approved results. Contact admin.')
        return redirect('matches:result_detail', pk=result_pk)

    team = user_team if user_team else fixture.home_team

    if request.method == 'POST':
        card_team_id = request.POST.get('card_team')
        if card_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=card_team_id)

        form = CardForm(fixture=fixture, is_admin=is_admin, data=request.POST, files=request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.result = result
            card.team = card.player.team
            card.save()
            if result.status == 'approved':
                _sync_player_stats(result)
            emoji = '🟨' if card.card_type == 'yellow' else '🟥'
            messages.success(request, f'{emoji} {card.get_card_type_display()} for {card.player.name} added!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = CardForm(fixture=fixture, is_admin=is_admin)

    players_dict = {p.id: p.team_id for p in Player.objects.filter(team__in=[fixture.home_team, fixture.away_team])}

    return render(request, 'matches/add_card.html', {
        'form': form, 'result': result, 'fixture': fixture,
        'home_team': fixture.home_team, 'away_team': fixture.away_team,
        'players_dict': players_dict,
        'is_admin': is_admin,
    })


@login_required
def add_rating(request, result_pk):
    """Add a top-rated player entry for a match result."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    if not is_team_member and not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if not is_admin and result.status == 'approved':
        messages.error(request, 'Cannot modify approved results. Contact admin.')
        return redirect('matches:result_detail', pk=result_pk)

    team = user_team if user_team else fixture.home_team

    if is_team_member and user_team:
        existing_count = result.ratings.filter(team=user_team).count()
    else:
        existing_count = result.ratings.count()

    max_ratings = 6 if is_admin else 3
    if existing_count >= max_ratings:
        if is_admin:
            messages.warning(request, 'Both teams already have 3 top-rated players each (6 total).')
        else:
            messages.warning(request, 'You already submitted 3 top-rated players for this match.')
        return redirect('matches:result_detail', pk=result_pk)

    if request.method == 'POST':
        rating_team_id = request.POST.get('rating_team')
        if rating_team_id:
            from teams.models import Team
            team = get_object_or_404(Team, pk=rating_team_id)

        form = PlayerRatingForm(fixture=fixture, is_admin=is_admin, data=request.POST, files=request.FILES)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.result = result
            rating.team = rating.player.team

            team_rating_count = result.ratings.filter(team=rating.team).count()
            if team_rating_count >= 3:
                messages.warning(request, f'{rating.team.name} already has 3 top-rated players for this match.')
                return redirect('matches:result_detail', pk=result_pk)

            rating.save()
            if result.status == 'approved':
                _sync_player_stats(result)
            messages.success(request, f'⭐ {rating.player.name} rated {rating.rating}/10!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = PlayerRatingForm(fixture=fixture, is_admin=is_admin)

    players_dict = {p.id: p.team_id for p in Player.objects.filter(team__in=[fixture.home_team, fixture.away_team])}

    return render(request, 'matches/add_rating.html', {
        'form': form, 'result': result, 'fixture': fixture,
        'home_team': fixture.home_team, 'away_team': fixture.away_team,
        'existing_count': existing_count,
        'players_dict': players_dict,
        'is_admin': is_admin,
    })


@login_required
def add_clean_sheet(request, result_pk):
    """Add a clean sheet for a specific GK.
    Validates that the GK's team conceded 0 goals in this match."""
    result = get_object_or_404(MatchResult, pk=result_pk)
    fixture = result.fixture

    user_team = getattr(request.user, 'team', None)
    is_admin = request.user.is_admin_user
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    if not is_team_member and not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if not is_admin and result.status == 'approved':
        messages.error(request, 'Cannot modify approved results. Contact admin.')
        return redirect('matches:result_detail', pk=result_pk)

    # Check which teams are eligible for a clean sheet (conceded 0)
    home_team = fixture.home_team
    away_team = fixture.away_team
    eligible_teams = []
    if result.away_score == 0:
        eligible_teams.append(home_team)
    if result.home_score == 0:
        eligible_teams.append(away_team)

    if not eligible_teams:
        messages.warning(request, '❌ No team is eligible for a clean sheet — both teams conceded goals.')
        return redirect('matches:result_detail', pk=result_pk)

    # Check if all eligible teams already have clean sheets assigned
    existing_cs = result.clean_sheets.values_list('team_id', flat=True)
    remaining_teams = [t for t in eligible_teams if t.pk not in existing_cs]
    if not remaining_teams:
        messages.info(request, '✅ Clean sheets already assigned for all eligible teams.')
        return redirect('matches:result_detail', pk=result_pk)

    if request.method == 'POST':
        form = CleanSheetForm(fixture=fixture, data=request.POST)
        if form.is_valid():
            cs = form.save(commit=False)
            cs.result = result
            cs.team = cs.player.team

            # Validate: the GK's team must have conceded 0
            goals_conceded_by_team = _get_goals_conceded(result, cs.team)
            if goals_conceded_by_team > 0:
                messages.error(request, f'❌ {cs.team.name} conceded {goals_conceded_by_team} goal(s) — not eligible for a clean sheet.')
                return redirect('matches:result_detail', pk=result_pk)

            # Validate: only 1 clean sheet per team per match
            if result.clean_sheets.filter(team=cs.team).exists():
                messages.warning(request, f'{cs.team.name} already has a clean sheet assigned for this match.')
                return redirect('matches:result_detail', pk=result_pk)

            # Validate: player must be a GK
            if cs.player.position != 'GK':
                messages.error(request, f'{cs.player.name} is not a Goalkeeper. Only GKs can earn clean sheets.')
                return redirect('matches:result_detail', pk=result_pk)

            cs.save()

            if result.status == 'approved':
                _sync_clean_sheet_stats_for_player(cs.player)

            messages.success(request, f'🧤 Clean sheet awarded to {cs.player.name}!')
            return redirect('matches:result_detail', pk=result_pk)
    else:
        form = CleanSheetForm(fixture=fixture)

    return render(request, 'matches/add_clean_sheet.html', {
        'form': form,
        'result': result,
        'fixture': fixture,
        'eligible_teams': eligible_teams,
        'is_admin': is_admin,
    })


def _get_goals_conceded(result, team):
    """How many goals did this team concede in the match?"""
    if team == result.fixture.home_team:
        return result.away_score
    else:
        return result.home_score


# ===== Delete Goal / Card / Rating / CleanSheet (Admin Only) =====

@login_required
def delete_goal(request, goal_pk):
    """Admin deletes a goal entry. Recalculates stats AND score."""
    goal = get_object_or_404(Goal, pk=goal_pk)
    result = goal.result

    if not request.user.is_admin_user:
        messages.error(request, 'Only admins can delete match events.')
        return redirect('matches:result_detail', pk=result.pk)

    if request.method == 'POST':
        scorer = goal.scorer
        assister = goal.assist
        scorer_name = scorer.name

        goal.delete()

        # Recalculate score from remaining goals
        _recalculate_score(result)

        # ALWAYS recalculate player stats (not just approved)
        scorer.total_goals = scorer.goals_scored.filter(result__status='approved').count()
        scorer.save(update_fields=['total_goals'])

        if assister:
            assister.total_assists = assister.assists.filter(result__status='approved').count()
            assister.save(update_fields=['total_assists'])

        messages.success(request, f'🗑️ Goal by {scorer_name} deleted. Score updated to {result.home_score}-{result.away_score}.')
    return redirect('matches:result_detail', pk=result.pk)


@login_required
def delete_card(request, card_pk):
    """Admin deletes a card entry."""
    card = get_object_or_404(Card, pk=card_pk)
    result = card.result

    if not request.user.is_admin_user:
        messages.error(request, 'Only admins can delete match events.')
        return redirect('matches:result_detail', pk=result.pk)

    if request.method == 'POST':
        player = card.player
        player_name = player.name

        card.delete()

        # ALWAYS recalculate player stats
        player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
        player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()
        player.save(update_fields=['total_red_cards', 'total_yellow_cards'])

        messages.success(request, f'🗑️ Card for {player_name} deleted.')
    return redirect('matches:result_detail', pk=result.pk)


@login_required
def delete_rating(request, rating_pk):
    """Admin deletes a rating entry."""
    rating = get_object_or_404(PlayerRating, pk=rating_pk)
    result = rating.result

    if not request.user.is_admin_user:
        messages.error(request, 'Only admins can delete match events.')
        return redirect('matches:result_detail', pk=result.pk)

    if request.method == 'POST':
        player = rating.player
        player_name = player.name

        rating.delete()

        # ALWAYS recalculate player stats
        ratings = player.match_ratings.filter(result__status='approved')
        player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
        player.save(update_fields=['avg_rating'])

        messages.success(request, f'🗑️ Rating for {player_name} deleted.')
    return redirect('matches:result_detail', pk=result.pk)


@login_required
def delete_clean_sheet(request, cs_pk):
    """Admin deletes a clean sheet entry."""
    cs = get_object_or_404(CleanSheet, pk=cs_pk)
    result = cs.result

    if not request.user.is_admin_user:
        messages.error(request, 'Only admins can delete match events.')
        return redirect('matches:result_detail', pk=result.pk)

    if request.method == 'POST':
        player = cs.player
        player_name = player.name

        cs.delete()

        # ALWAYS recalculate player stats
        _sync_clean_sheet_stats_for_player(player)

        messages.success(request, f'🗑️ Clean sheet for {player_name} removed.')
    return redirect('matches:result_detail', pk=result.pk)


def result_detail(request, pk):
    """View match result details."""
    result = get_object_or_404(MatchResult, pk=pk)
    fixture = result.fixture
    goals = result.goals.all()
    cards = result.cards.all()
    ratings = result.ratings.all()
    clean_sheets = result.clean_sheets.select_related('player', 'team').all()

    # Determine permissions
    is_admin = request.user.is_authenticated and request.user.is_admin_user
    user_team = getattr(request.user, 'team', None) if request.user.is_authenticated else None
    is_team_member = user_team and (user_team == fixture.home_team or user_team == fixture.away_team)

    can_add_events = is_admin or (is_team_member and result.status != 'approved')
    can_edit_result = is_admin
    can_delete_events = is_admin

    # Check if clean sheet button should be shown
    # Eligible if any team conceded 0 and doesn't already have a CS assigned
    can_add_clean_sheet = False
    if can_add_events:
        existing_cs_teams = set(clean_sheets.values_list('team_id', flat=True))
        if result.away_score == 0 and fixture.home_team.pk not in existing_cs_teams:
            can_add_clean_sheet = True
        if result.home_score == 0 and fixture.away_team.pk not in existing_cs_teams:
            can_add_clean_sheet = True

    return render(request, 'matches/result_detail.html', {
        'result': result,
        'goals': goals,
        'cards': cards,
        'ratings': ratings,
        'clean_sheets': clean_sheets,
        'can_add_events': can_add_events,
        'can_edit_result': can_edit_result,
        'can_delete_events': can_delete_events,
        'can_add_clean_sheet': can_add_clean_sheet,
        'is_admin': is_admin,
        'is_team_member': is_team_member,
    })


def result_list(request):
    """List all approved results."""
    results = MatchResult.objects.filter(status='approved')
    return render(request, 'matches/result_list.html', {'results': results})


# ===== Leaderboards =====

def leaderboard(request):
    """Public leaderboard with per-league filtering."""
    from tournaments.models import League

    # Get all leagues for the selector
    leagues = League.objects.select_related('tournament').filter(
        tournament__is_active=True
    ).order_by('tournament__name', 'name')

    league_pk = request.GET.get('league')
    selected_league = None

    if league_pk:
        # Per-league stats: query from Goal/Card/Rating records for that league
        selected_league = get_object_or_404(League, pk=league_pk)
        league_filter = Q(result__fixture__league=selected_league, result__status='approved')

        # Top scorers: count goals per scorer in this league
        top_scorers = Player.objects.filter(
            goals_scored__result__fixture__league=selected_league,
            goals_scored__result__status='approved'
        ).annotate(
            league_goals=Count('goals_scored', filter=league_filter)
        ).filter(league_goals__gt=0).order_by('-league_goals')[:20]

        # Top assists
        top_assists = Player.objects.filter(
            assists__result__fixture__league=selected_league,
            assists__result__status='approved'
        ).annotate(
            league_assists=Count('assists', filter=league_filter)
        ).filter(league_assists__gt=0).order_by('-league_assists')[:20]

        # Top rated
        top_rated = Player.objects.filter(
            match_ratings__result__fixture__league=selected_league,
            match_ratings__result__status='approved'
        ).annotate(
            league_avg_rating=Avg('match_ratings__rating', filter=league_filter)
        ).filter(league_avg_rating__gt=0).order_by('-league_avg_rating')[:20]

        # Most cards
        most_cards = Player.objects.filter(
            cards__result__fixture__league=selected_league,
            cards__result__status='approved'
        ).annotate(
            league_red_cards=Count('cards', filter=league_filter & Q(cards__card_type='red')),
            league_yellow_cards=Count('cards', filter=league_filter & Q(cards__card_type='yellow')),
        ).filter(
            Q(league_red_cards__gt=0) | Q(league_yellow_cards__gt=0)
        ).order_by('-league_red_cards', '-league_yellow_cards')[:20]

        # Top clean sheets
        cs_filter = Q(clean_sheet_records__result__fixture__league=selected_league,
                      clean_sheet_records__result__status='approved')
        top_clean_sheets = Player.objects.filter(
            clean_sheet_records__result__fixture__league=selected_league,
            clean_sheet_records__result__status='approved',
            position='GK'
        ).annotate(
            league_clean_sheets=Count('clean_sheet_records', filter=cs_filter)
        ).filter(league_clean_sheets__gt=0).order_by('-league_clean_sheets')[:20]

    else:
        # Global stats: use cached fields on Player
        top_scorers = Player.objects.select_related('team').filter(total_goals__gt=0).order_by('-total_goals')[:20]
        top_assists = Player.objects.select_related('team').filter(total_assists__gt=0).order_by('-total_assists')[:20]
        top_rated = Player.objects.select_related('team').filter(avg_rating__gt=0).order_by('-avg_rating')[:20]
        most_cards = Player.objects.select_related('team').filter(
            Q(total_red_cards__gt=0) | Q(total_yellow_cards__gt=0)
        ).order_by('-total_red_cards', '-total_yellow_cards')[:20]
        top_clean_sheets = Player.objects.select_related('team').filter(
            total_clean_sheets__gt=0, position='GK'
        ).order_by('-total_clean_sheets')[:20]

    return render(request, 'matches/leaderboard.html', {
        'top_scorers': top_scorers,
        'top_assists': top_assists,
        'top_rated': top_rated,
        'most_cards': most_cards,
        'top_clean_sheets': top_clean_sheets,
        'leagues': leagues,
        'selected_league': selected_league,
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


# ===== Admin Views & Stats Sync =====

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


def _sync_clean_sheet_stats(result):
    """Recalculate clean sheet counts for all GKs involved in this result."""
    for cs in result.clean_sheets.all():
        _sync_clean_sheet_stats_for_player(cs.player)


def _sync_clean_sheet_stats_for_player(player):
    """Recalculate total_clean_sheets for a specific player from CleanSheet records."""
    player.total_clean_sheets = player.clean_sheet_records.filter(
        result__status='approved'
    ).count()
    player.save(update_fields=['total_clean_sheets'])


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

    # Sync all stats
    _sync_player_stats(result)
    _sync_clean_sheet_stats(result)

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
