from itertools import combinations
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from .models import Tournament, TournamentApplication, League, Fixture
from .forms import TournamentForm, LeagueForm, FixtureForm
from .utils import get_league_standings
from teams.models import Team


def tournament_list(request):
    """Public list of tournaments."""
    tournaments = Tournament.objects.exclude(status='draft')
    return render(request, 'tournaments/tournament_list.html', {'tournaments': tournaments})


def tournament_detail(request, pk):
    """Public tournament detail page."""
    tournament = get_object_or_404(Tournament, pk=pk)
    leagues = tournament.leagues.all()

    # Check if current user's team has applied
    user_application = None
    user_team = None
    if request.user.is_authenticated:
        user_team = getattr(request.user, 'team', None)
        if user_team:
            user_application = TournamentApplication.objects.filter(
                tournament=tournament, team=user_team
            ).first()

    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'leagues': leagues,
        'user_application': user_application,
        'user_team': user_team,
    })


# ===== Browse & Apply =====

@login_required
def browse_tournaments(request):
    """Browse all open tournaments that verified teams can apply to."""
    open_tournaments = Tournament.objects.filter(
        is_open=True, is_active=True
    ).exclude(status='draft').annotate(
        accepted_count=Count('applications', filter=Q(applications__status='accepted'))
    )

    user_team = getattr(request.user, 'team', None)
    team_is_verified = user_team and user_team.is_approved

    # Get existing applications for the user's team
    existing_applications = {}
    if user_team:
        for app in TournamentApplication.objects.filter(team=user_team).select_related('tournament'):
            existing_applications[app.tournament_id] = app

    # Build tournament data with join status
    tournament_data = []
    for t in open_tournaments:
        app = existing_applications.get(t.id)
        join_status = None
        if app:
            join_status = app.status  # pending, accepted, rejected

        tournament_data.append({
            'tournament': t,
            'application': app,
            'join_status': join_status,
            'entry_gate_closed': t.entry_gate_closed,
            'is_tournament_full': t.accepted_count >= t.max_teams,
        })

    return render(request, 'tournaments/browse.html', {
        'tournament_data': tournament_data,
        'team_is_verified': team_is_verified,
        'user_team': user_team,
    })


@login_required
def apply_tournament(request, pk):
    """Apply to join a tournament."""
    tournament = get_object_or_404(Tournament, pk=pk, is_open=True)

    user_team = getattr(request.user, 'team', None)
    if not user_team or not user_team.is_approved:
        messages.error(request, '❌ You need a verified team to apply.')
        return redirect('tournaments:browse')

    # Validation: deadline
    if tournament.entry_gate_closed:
        messages.error(request, '⏰ Registration deadline has passed.')
        return redirect('tournaments:browse')

    # Validation: capacity
    if tournament.is_tournament_full:
        messages.error(request, '🚫 Tournament is full.')
        return redirect('tournaments:browse')

    # Validation: already applied
    already_applied = TournamentApplication.objects.filter(
        tournament=tournament, team=user_team
    ).exists()
    if already_applied:
        messages.info(request, 'You have already applied to this tournament.')
        return redirect('tournaments:browse')

    # Create application
    TournamentApplication.objects.create(
        tournament=tournament,
        team=user_team,
        status='pending',
    )
    messages.success(request, f'🎯 Applied to "{tournament.name}"! Awaiting admin review.')
    return redirect('tournaments:browse')


def all_standings(request):
    """View standings for all leagues across all active tournaments."""
    leagues = League.objects.select_related('tournament').filter(
        tournament__is_active=True
    ).order_by('tournament__name', 'name')

    league_data = []
    for league in leagues:
        standings = get_league_standings(league)
        if standings:
            league_data.append({
                'league': league,
                'tournament': league.tournament,
                'standings': standings,
            })

    return render(request, 'tournaments/all_standings.html', {
        'league_data': league_data,
    })


def league_standings(request, pk):
    """View league standings."""
    league = get_object_or_404(League, pk=pk)
    sorted_standings = get_league_standings(league)

    return render(request, 'tournaments/league_standings.html', {
        'league': league,
        'standings': sorted_standings,
        'tournament': league.tournament,
    })


@login_required
def download_league_standings_pdf(request, pk):
    """Download league standings as PDF (Admin only)."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=pk)
    sorted_standings = get_league_standings(league)

    return render(request, 'tournaments/pdf_standings.html', {
        'league': league,
        'tournament': league.tournament,
        'standings': sorted_standings
    })


@login_required
def download_league_teams_pdf(request, pk):
    """Download list of teams in a league as PDF (Admin only)."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=pk)
    teams = league.teams.all()

    return render(request, 'tournaments/pdf_league_teams.html', {
        'league': league,
        'tournament': league.tournament,
        'teams': teams
    })


def league_fixtures(request, pk):
    """View league fixtures."""
    league = get_object_or_404(League, pk=pk)
    fixtures = league.fixtures.all()
    matchdays = sorted(set(fixtures.values_list('matchday', flat=True)))

    fixtures_by_matchday = {}
    for md in matchdays:
        fixtures_by_matchday[md] = fixtures.filter(matchday=md)

    return render(request, 'tournaments/league_fixtures.html', {
        'league': league,
        'fixtures_by_matchday': fixtures_by_matchday,
        'tournament': league.tournament,
    })


def download_matchday_fixtures(request, league_pk, matchday):
    """Download fixtures for a specific matchday."""
    import logging
    try:
        league = get_object_or_404(League, pk=league_pk)
        fixtures = league.fixtures.filter(matchday=matchday).select_related('home_team', 'away_team', 'result')
        
        return render(request, 'tournaments/pdf_matchday_fixtures.html', {
            'league': league,
            'tournament': league.tournament,
            'matchday': matchday,
            'fixtures': fixtures
        })
    except Exception as e:
        logging.error(f"Error in download_matchday_fixtures: {e}")
        return HttpResponse(f"Server Error: {str(e)}", status=500)


# ===== Admin Views =====

@login_required
def admin_create_tournament(request):
    """Admin creates a new tournament."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '🏆 Tournament created!')
            return redirect('tournaments:tournament_list')
    else:
        form = TournamentForm()

    return render(request, 'tournaments/admin_create.html', {'form': form})


@login_required
def admin_edit_tournament(request, pk):
    """Admin edits tournament."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    tournament = get_object_or_404(Tournament, pk=pk)

    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tournament updated!')
            return redirect('tournaments:tournament_detail', pk=pk)
    else:
        form = TournamentForm(instance=tournament)

    return render(request, 'tournaments/admin_edit.html', {'form': form, 'tournament': tournament})


@login_required
def admin_add_league(request, tournament_pk):
    """Admin adds a league to a tournament."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    if request.method == 'POST':
        form = LeagueForm(request.POST)
        if form.is_valid():
            league = form.save(commit=False)
            league.tournament = tournament
            league.save()
            messages.success(request, f'League "{league.name}" added!')
            return redirect('tournaments:tournament_detail', pk=tournament_pk)
    else:
        form = LeagueForm()

    return render(request, 'tournaments/admin_add_league.html', {
        'form': form, 'tournament': tournament
    })


@login_required
def admin_assign_teams(request, league_pk):
    """Admin assigns teams to a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=league_pk)
    available_teams = Team.objects.filter(status='approved').exclude(
        leagues=league
    )
    assigned_teams = league.teams.all()

    if request.method == 'POST':
        team_ids = request.POST.getlist('teams')
        for tid in team_ids:
            try:
                team = Team.objects.get(pk=tid, status='approved')
                if not league.is_full:
                    league.teams.add(team)
            except Team.DoesNotExist:
                pass
        messages.success(request, 'Teams assigned!')
        return redirect('tournaments:admin_assign_teams', league_pk=league_pk)

    return render(request, 'tournaments/admin_assign_teams.html', {
        'league': league,
        'available_teams': available_teams,
        'assigned_teams': assigned_teams,
        'tournament': league.tournament,
    })


@login_required
def admin_remove_team(request, league_pk, team_pk):
    """Admin removes a team from a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=league_pk)
    team = get_object_or_404(Team, pk=team_pk)
    league.teams.remove(team)
    messages.success(request, f'{team.name} removed from {league.name}.')
    return redirect('tournaments:admin_assign_teams', league_pk=league_pk)


@login_required
def admin_generate_fixtures(request, league_pk):
    """Generate round-robin fixtures for a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=league_pk)
    teams = list(league.teams.all())

    if len(teams) < 2:
        messages.error(request, 'Need at least 2 teams to generate fixtures.')
        return redirect('tournaments:admin_assign_teams', league_pk=league_pk)

    # Delete existing fixtures
    league.fixtures.all().delete()

    # Round-robin scheduling algorithm
    n = len(teams)
    if n % 2 != 0:
        teams.append(None)  # BYE
        n += 1

    rounds = n - 1
    half = n // 2

    team_indices = list(range(n))
    is_2leg = league.format == 'round_robin_2leg'

    matchday = 1
    for round_num in range(rounds):
        for i in range(half):
            t1 = team_indices[i]
            t2 = team_indices[n - 1 - i]

            if teams[t1] is not None and teams[t2] is not None:
                # First leg
                Fixture.objects.create(
                    league=league,
                    home_team=teams[t1],
                    away_team=teams[t2],
                    matchday=matchday,
                )
                
                # Second leg
                if is_2leg:
                    Fixture.objects.create(
                        league=league,
                        home_team=teams[t2],
                        away_team=teams[t1],
                        matchday=matchday + rounds,
                    )

        matchday += 1
        # Rotate: fix first team, rotate rest
        team_indices = [team_indices[0]] + [team_indices[-1]] + team_indices[1:-1]

    messages.success(request, f'🎯 {league.fixtures.count()} fixtures generated!')
    return redirect('tournaments:league_fixtures', pk=league_pk)


@login_required
def admin_add_fixture(request, league_pk):
    """Admin adds a fixture manually to a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=league_pk)

    if request.method == 'POST':
        form = FixtureForm(league, request.POST)
        if form.is_valid():
            fixture = form.save(commit=False)
            fixture.league = league
            fixture.save()
            messages.success(request, 'Fixture added!')
            return redirect('tournaments:league_fixtures', pk=league_pk)
    else:
        form = FixtureForm(league)

    return render(request, 'tournaments/admin_add_fixture.html', {
        'form': form, 'league': league, 'tournament': league.tournament
    })


# ===== Admin Application Management =====

@login_required
def admin_applications(request, tournament_pk):
    """Admin views and manages tournament applications."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    status_filter = request.GET.get('status', 'pending')

    applications = tournament.applications.select_related('team', 'assigned_league')
    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    leagues = tournament.leagues.all()

    return render(request, 'tournaments/admin_applications.html', {
        'tournament': tournament,
        'applications': applications,
        'status_filter': status_filter,
        'leagues': leagues,
    })


@login_required
def admin_accept_application(request, app_pk):
    """Accept a tournament application and assign to a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    application = get_object_or_404(TournamentApplication, pk=app_pk)
    tournament = application.tournament

    if request.method == 'POST':
        league_id = request.POST.get('league')
        if not league_id:
            messages.error(request, 'Please select a league to assign the team to.')
            return redirect('tournaments:admin_applications', tournament_pk=tournament.pk)

        league = get_object_or_404(League, pk=league_id, tournament=tournament)

        if league.is_full:
            messages.error(request, f'"{league.name}" is full.')
            return redirect('tournaments:admin_applications', tournament_pk=tournament.pk)

        # Accept the application
        application.status = 'accepted'
        application.assigned_league = league
        application.reviewed_at = timezone.now()
        application.save()

        # Add team to the league roster
        league.teams.add(application.team)

        messages.success(request, f'✅ {application.team.name} accepted & assigned to {league.name}!')

    return redirect('tournaments:admin_applications', tournament_pk=tournament.pk)


@login_required
def admin_reject_application(request, app_pk):
    """Reject a tournament application."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    application = get_object_or_404(TournamentApplication, pk=app_pk)

    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        application.status = 'rejected'
        application.admin_notes = notes
        application.reviewed_at = timezone.now()
        application.save()
        messages.success(request, f'❌ {application.team.name} application rejected.')

    return redirect('tournaments:admin_applications', tournament_pk=application.tournament.pk)


@login_required
def admin_dashboard(request):
    """Admin dashboard with overview stats."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    from matches.models import MatchResult

    pending_applications = TournamentApplication.objects.filter(status='pending').count()

    context = {
        'total_tournaments': Tournament.objects.count(),
        'active_tournaments': Tournament.objects.filter(status='ongoing').count(),
        'pending_teams': Team.objects.filter(status='pending').count(),
        'approved_teams': Team.objects.filter(status='approved').count(),
        'pending_results': MatchResult.objects.filter(status='pending').count(),
        'pending_applications': pending_applications,
        'total_fixtures': Fixture.objects.count(),
        'completed_fixtures': Fixture.objects.filter(status='completed').count(),
        'recent_tournaments': Tournament.objects.all()[:5],
        'recent_pending_teams': Team.objects.filter(status='pending')[:5],
        'recent_pending_results': MatchResult.objects.filter(status='pending')[:5],
        'recent_applications': TournamentApplication.objects.filter(status='pending').select_related('team', 'tournament')[:5],
    }
    return render(request, 'tournaments/admin_dashboard.html', context)
