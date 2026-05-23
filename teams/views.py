import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Sum, Max, Q
from django.utils.text import slugify
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import random
import string
from .models import Team, Player, Trophy, TransferWindow, TransferRequest, TransferHistory, PlayerRegistration
from .forms import TeamForm, PlayerForm, AdminPlayerForm, AdminTeamForm
from .services import TransferService
from .exceptions import TransferError

def player_card(request, pk):
    """View to generate an E-Sports style Player Card."""
    player = get_object_or_404(Player, pk=pk)
    return render(request, 'teams/player_card.html', {'player': player})

@login_required
def register_team(request):
    """Register a new team."""
    # Check if user already has a team (bulletproof check)
    try:
        if getattr(request.user, 'team', None):
            messages.warning(request, 'You already have a registered team.')
            return redirect('teams:my_team')
    except Exception:
        # If any error occurs (like RelatedObjectDoesNotExist or AttributeError), assume no team
        pass

    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user
            try:
                team.save()
                messages.success(request, '🎉 Team registered successfully! Awaiting admin verification.')
                return redirect('teams:my_team')
            except IntegrityError:
                form.add_error(None, 'A database error occurred. Ensure your team name is unique or that you do not already have a team.')
            except Exception as e:
                form.add_error(None, f'System error during save (e.g. file upload failed): {str(e)}')
    else:
        form = TeamForm()

    return render(request, 'teams/register_team.html', {'form': form})


@login_required
def my_team(request):
    """View the user's team dashboard."""
    try:
        team = request.user.team
    except Team.DoesNotExist:
        messages.info(request, 'You haven\'t registered a team yet.')
        return redirect('teams:register_team')

    players = team.players.all()
    from matches.models import Goal, Card, MatchResult
    from tournaments.models import Fixture
    
    # Accurate Team Stats (Calculated from match events where this team was involved)
    team_stats = {
        'total_goals': Goal.objects.filter(team=team, result__status='approved').count(),
        'total_assists': Goal.objects.filter(team=team, result__status='approved').exclude(assist=None).count(),
        'total_yellow_cards': Card.objects.filter(team=team, card_type='yellow', result__status='approved').count(),
        'total_red_cards': Card.objects.filter(team=team, card_type='red', result__status='approved').count(),
        'max_matches': Fixture.objects.filter(
            Q(home_team=team) | Q(away_team=team),
            status='completed'
        ).count(),
    }

    # Tournament applications
    applications = team.tournament_applications.select_related(
        'tournament', 'assigned_league'
    ).all()

    # Active tournaments (Directly from leagues the team is part of)
    active_tournaments = []
    for league in team.leagues.select_related('tournament').all():
        active_tournaments.append({
            'tournament': league.tournament,
            'league': league,
            'fixtures_count': league.fixtures.count(),
            'completed_count': league.fixtures.filter(status='completed').count(),
            'progress_percent': int((league.fixtures.filter(status='completed').count() / league.fixtures.count() * 100)) if league.fixtures.count() > 0 else 0,
        })

    # Performance Trends (Cumulative Points for the first active league)
    performance_data = {'labels': [], 'data': []}
    if active_tournaments:
        first_active = active_tournaments[0]['league']
        perf_fixtures = first_active.fixtures.filter(
            Q(home_team=team) | Q(away_team=team),
            status='completed'
        ).select_related('result').order_by('matchday')
        
        c_points = 0
        t_pts = first_active.tournament
        for f in perf_fixtures:
            res = f.result
            if f.home_team == team:
                if res.home_score > res.away_score: c_points += t_pts.points_win
                elif res.home_score == res.away_score: c_points += t_pts.points_draw
                else: c_points += t_pts.points_loss
            else:
                if res.away_score > res.home_score: c_points += t_pts.points_win
                elif res.home_score == res.away_score: c_points += t_pts.points_draw
                else: c_points += t_pts.points_loss
            
            performance_data['labels'].append(f"MD {f.matchday}")
            performance_data['data'].append(c_points)

    # Matches logic
    from tournaments.models import Fixture
    
    # Recent results (last 5)
    recent_results = Fixture.objects.filter(
        Q(home_team=team) | Q(away_team=team),
        status='completed'
    ).select_related(
        'home_team', 'away_team', 'result', 'league', 'league__tournament'
    ).order_by('-matchday', '-created_at')[:5]

    # Upcoming matches (next 5)
    upcoming_matches = Fixture.objects.filter(
        Q(home_team=team) | Q(away_team=team)
    ).exclude(status='completed').select_related(
        'home_team', 'away_team', 'league', 'league__tournament'
    ).order_by('matchday')[:5]

    # Enhanced Player data with ratings history for charts
    for p in players:
        p.ratings_history = list(p.match_ratings.filter(
            result__status='approved'
        ).order_by('result__fixture__matchday').values_list('rating', flat=True))

    return render(request, 'teams/my_team.html', {
        'team': team,
        'players': players,
        'team_stats': team_stats,
        'applications': applications,
        'active_tournaments': active_tournaments,
        'upcoming_matches': upcoming_matches,
        'recent_results': recent_results,
        'performance_data': performance_data,
    })



@login_required
def add_player(request):
    """Add a player to the user's team."""
    try:
        team = request.user.team
    except Team.DoesNotExist:
        messages.error(request, 'You need to register a team first.')
        return redirect('teams:register_team')

    # Roster lock check
    if team.is_roster_locked:
        messages.warning(request, '🔒 Roster is locked — your team has been accepted into an active tournament.')
        return redirect('teams:my_team')

    if team.player_count >= 30:
        messages.warning(request, 'Maximum roster size (30 players) reached.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.team = team
            
            # Auto-generate gaming ID if blank
            if not player.gaming_id:
                base_id = slugify(f"{team.name}_{player.name}").replace('-', '_')
                unique_id = base_id
                while Player.objects.filter(gaming_id=unique_id).exists():
                    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                    unique_id = f"{base_id}_{suffix}"
                player.gaming_id = unique_id
                
            player.save()
            messages.success(request, f'✅ {player.name} added to the roster!')
            return redirect('teams:my_team')
    else:
        form = PlayerForm()

    return render(request, 'teams/add_player.html', {'form': form, 'team': team})


@login_required
def edit_player(request, pk):
    """Edit a player. Allowed for team captain or admin."""
    if request.user.is_admin_user:
        player = get_object_or_404(Player, pk=pk)
        form_class = AdminPlayerForm
    else:
        player = get_object_or_404(Player, pk=pk, team__captain=request.user)
        form_class = PlayerForm

    # Roster lock check (Admins can bypass lock)
    if player.team.is_roster_locked and not request.user.is_admin_user:
        messages.warning(request, '🔒 Roster is locked — cannot edit players during an active tournament.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ {player.name} updated!')
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('teams:my_team')
    else:
        form = form_class(instance=player)

    return render(request, 'teams/edit_player.html', {'form': form, 'player': player})


@login_required
def delete_player(request, pk):
    """Remove a player from roster. Allowed for team captain or admin."""
    if request.user.is_admin_user:
        player = get_object_or_404(Player, pk=pk)
    else:
        player = get_object_or_404(Player, pk=pk, team__captain=request.user)

    # Roster lock check (Admins can bypass lock)
    if player.team.is_roster_locked and not request.user.is_admin_user:
        messages.warning(request, '🔒 Roster is locked — cannot remove players during an active tournament.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        name = player.name
        player.delete()
        messages.success(request, f'🗑️ {name} removed from roster.')
        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
    return redirect('teams:my_team')


def team_list(request):
    """Public list of all approved teams."""
    teams = Team.objects.filter(status='approved')
    return render(request, 'teams/team_list.html', {'teams': teams})


def team_detail(request, pk):
    """Public team detail page."""
    team = get_object_or_404(Team, pk=pk)
    players = team.players.filter(is_active=True)
    return render(request, 'teams/team_detail.html', {'team': team, 'players': players})


# ===== Admin Views =====

@login_required
def admin_verify_teams(request):
    """Admin view to verify pending teams."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    status_filter = request.GET.get('status', 'pending')
    teams = Team.objects.all()
    if status_filter != 'all':
        teams = teams.filter(status=status_filter)

    return render(request, 'teams/admin_verify.html', {'teams': teams, 'status_filter': status_filter})


@login_required
def admin_approve_team(request, pk):
    """Approve a team."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    team = get_object_or_404(Team, pk=pk)
    team.status = 'approved'
    team.rejection_reason = ''
    team.save()
    messages.success(request, f'✅ Team "{team.name}" approved!')
    return redirect('teams:admin_verify')


@login_required
def admin_reject_team(request, pk):
    """Reject a team with reason."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided.')
        team.status = 'rejected'
        team.rejection_reason = reason
        team.save()
        messages.success(request, f'❌ Team "{team.name}" rejected.')
    return redirect('teams:admin_verify')


@login_required
def download_team_roster_pdf(request, pk):
    """Download team roster as PDF (Admin only)."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    team = get_object_or_404(Team, pk=pk)
    players = team.players.all()

    return render(request, 'teams/pdf_team_roster.html', {
        'team': team,
        'players': players
    })


@login_required
def admin_add_player(request, team_pk):
    """Admin view to add a player to any team."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    team = get_object_or_404(Team, pk=team_pk)

    if request.method == 'POST':
        form = AdminPlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.team = team
            
            # Auto-generate gaming ID if blank
            if not player.gaming_id:
                base_id = slugify(f"{team.name}_{player.name}").replace('-', '_')
                unique_id = base_id
                while Player.objects.filter(gaming_id=unique_id).exists():
                    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                    unique_id = f"{base_id}_{suffix}"
                player.gaming_id = unique_id
                
            player.save()
            messages.success(request, f'✅ {player.name} added to {team.name} roster!')
            return redirect('teams:team_detail', pk=team.pk)
    else:
        form = AdminPlayerForm()

    return render(request, 'teams/add_player.html', {
        'form': form, 
        'team': team,
        'is_admin': True
    })

# ===== Transfer System Views =====

@login_required
def transfer_hub(request):
    """Transfer Market Dashboard."""
    window = TransferWindow.objects.filter(is_active=True).first()
    
    # Use is_open property for accurate window status
    effective_window = window if (window and window.is_open) else None

    # All active players with optimized queries
    players = Player.objects.filter(
        is_active=True
    ).select_related('team').order_by('team__name', 'name')
    
    incoming_requests = []
    outgoing_requests = []
    user_team = getattr(request.user, 'team', None)
    
    if user_team:
        incoming_requests = user_team.incoming_transfers.select_related(
            'player', 'from_team', 'to_team', 'window'
        ).exclude(status__in=['COMPLETED', 'REJECTED', 'CANCELLED'])
        outgoing_requests = user_team.outgoing_transfers.select_related(
            'player', 'from_team', 'to_team', 'window'
        ).exclude(status__in=['COMPLETED', 'REJECTED', 'CANCELLED'])
    
    # Global transfer history — visible to all users
    transfer_history = TransferHistory.objects.select_related(
        'player', 'player__team', 'from_team', 'to_team'
    ).order_by('-transfer_date')[:5]
    
    admin_pending = []
    if request.user.is_admin_user:
        admin_pending = TransferRequest.objects.filter(
            status='SELLING_APPROVED'
        ).select_related('player', 'from_team', 'to_team', 'window')
        
    return render(request, 'teams/transfer_hub.html', {
        'window': effective_window,
        'players': players,
        'user_team': user_team,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'admin_pending': admin_pending,
        'transfer_history': transfer_history,
    })

@login_required
def all_transfers(request):
    """View all transfer history."""
    transfer_history = TransferHistory.objects.select_related(
        'player', 'player__team', 'from_team', 'to_team'
    ).order_by('-transfer_date')
    
    return render(request, 'teams/all_transfers.html', {
        'transfer_history': transfer_history,
    })

@login_required
def export_transfers_pdf(request):
    """Download transfer history as PDF."""
    transfer_history = TransferHistory.objects.select_related(
        'player', 'player__team', 'from_team', 'to_team'
    ).order_by('-transfer_date')
    
    return render(request, 'teams/pdf_transfers.html', {
        'transfer_history': transfer_history
    })

@login_required
def request_transfer(request, player_id):
    """Initiate a transfer request via the service layer."""
    if request.method != 'POST':
        return redirect('teams:transfer_hub')
        
    window = TransferWindow.objects.filter(is_active=True).first()
    user_team = getattr(request.user, 'team', None)
    
    if not user_team:
        messages.error(request, 'Only team captains can request transfers.')
        return redirect('teams:transfer_hub')
        
    player = get_object_or_404(Player, pk=player_id)
    fee = request.POST.get('fee', 0)
    transfer_type = request.POST.get('transfer_type', 'permanent')
    loan_end_date = request.POST.get('loan_end_date') or None
    
    # Parse loan_end_date if provided
    if loan_end_date:
        from datetime import datetime
        try:
            loan_end_date = datetime.strptime(loan_end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid loan end date format.')
            return redirect('teams:transfer_hub')
    
    try:
        TransferService.initiate_transfer(
            player=player,
            from_team=player.team,
            to_team=user_team,
            requested_by=request.user,
            window=window,
            transfer_type=transfer_type,
            fee=fee,
            loan_end_date=loan_end_date,
        )
        messages.success(request, f'Transfer request sent for {player.name}!')
    except TransferError as e:
        messages.error(request, str(e))
    
    return redirect('teams:transfer_hub')

@login_required
def transfer_action(request, request_id, action):
    """Approve, reject, or cancel a transfer via the service layer."""
    transfer = get_object_or_404(
        TransferRequest.objects.select_related(
            'player', 'from_team', 'to_team', 'window'
        ),
        pk=request_id,
    )
    
    reason = request.POST.get('reason', '') if request.method == 'POST' else ''
    
    try:
        result = TransferService.process_approval(
            transfer_request=transfer,
            user=request.user,
            action=action,
            reason=reason,
        )
        if action == 'reject':
            messages.info(request, result)
        else:
            messages.success(request, result)
    except TransferError as e:
        messages.error(request, str(e))
    
    return redirect('teams:transfer_hub')

@login_required
def admin_toggle_transfer_window(request):
    """Admin action to open/close the latest transfer window."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
        
    window = TransferWindow.objects.last()
    if not window:
        messages.error(request, 'No transfer windows exist. Creating a default one...')
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        window = TransferWindow.objects.create(
            season="Default Season",
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True
        )
        messages.success(request, 'Default Transfer Window created and opened!')
    else:
        window.is_active = not window.is_active
        window.save()
        status = 'OPENED' if window.is_active else 'CLOSED'
        messages.success(request, f'Transfer Window {status} successfully.')
        
    return redirect(request.META.get('HTTP_REFERER', 'tournaments:admin_dashboard'))

@login_required
def admin_initialize_transfer_window(request):
    """Explicitly create a new transfer window."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    if request.method == 'POST':
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        TransferWindow.objects.create(
            season=request.POST.get('season', 'New Season'),
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True
        )
        messages.success(request, 'New Transfer Window initialized!')
        
    return redirect('tournaments:admin_dashboard')

@login_required
def api_notifications(request):
    """Returns JSON payload with user notifications for JS polling."""
    data = {'transfers': 0, 'results': 0, 'messages': []}
    
    if not hasattr(request.user, 'team'):
        return JsonResponse(data)
        
    team = request.user.team
    
    # Check pending incoming transfers
    pending_transfers = TransferRequest.objects.filter(
        from_team=team, 
        status='PENDING'
    ).count()
    
    if pending_transfers > 0:
        data['transfers'] = pending_transfers
        data['messages'].append(f'You have {pending_transfers} pending transfer requests.')
        
    # We can also check pending match results that require approval if needed.
    
    return JsonResponse(data)


@login_required
def admin_manage_team_finances(request, pk):
    """Admin view to manage team budget, status, and player values in bulk."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    team = get_object_or_404(Team, pk=pk)
    players = team.players.all()

    if request.method == 'POST':
        # 1. Update Team details (Budget and Status)
        budget = request.POST.get('budget', team.budget)
        status = request.POST.get('status', team.status)
        
        try:
            team.budget = budget
            team.status = status
            team.save()
        except Exception as e:
            messages.error(request, f'Error saving team finances: {str(e)}')
            return redirect('teams:admin_manage_team_finances', pk=pk)

        # 2. Check for Auto-Setup actions
        auto_setup = request.POST.get('auto_setup')
        if auto_setup:
            count = players.count()
            if count > 0:
                from decimal import Decimal
                if auto_setup == 'equal':
                    # Distribute budget equally
                    equal_value = Decimal(str(team.budget)) / count
                    for player in players:
                        player.value = equal_value
                        player.save()
                    messages.success(request, f'Distributed budget of ${team.budget:,.0f} equally among {count} players (${equal_value:,.0f} each).')
                elif auto_setup == 'flat_1m':
                    for player in players:
                        player.value = Decimal('1000000')
                        player.save()
                    messages.success(request, f'Set value of all {count} players to $1,000,000.')
                elif auto_setup == 'flat_100k':
                    for player in players:
                        player.value = Decimal('100000')
                        player.save()
                    messages.success(request, f'Set value of all {count} players to $100,000.')
                elif auto_setup == 'reset':
                    for player in players:
                        player.value = Decimal('0')
                        player.save()
                    messages.success(request, f'Reset value of all {count} players to $0.')
            else:
                messages.warning(request, 'No players in squad to set up.')
            return redirect('teams:admin_manage_team_finances', pk=pk)

        # 3. Update Individual Player Values
        updated_count = 0
        for player in players:
            val_input = request.POST.get(f'player_value_{player.pk}')
            if val_input is not None:
                try:
                    from decimal import Decimal
                    new_val = Decimal(val_input)
                    if player.value != new_val:
                        player.value = new_val
                        player.save()
                        updated_count += 1
                except (ValueError, TypeError, ArithmeticError):
                    pass

        messages.success(request, f'Successfully updated team finances and {updated_count} player values.')
        return redirect('teams:team_detail', pk=pk)

    return render(request, 'teams/admin_manage_finances.html', {
        'team': team,
        'players': players,
    })


# ===== Transfer REST API =====

import json
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from .serializers import (
    serialize_transfer_request,
    serialize_transfer_window,
    serialize_transfer_history,
    validate_initiate_payload,
)


def _json_error(message, status=400):
    """Helper to return a standardized JSON error response."""
    return JsonResponse({'success': False, 'error': str(message)}, status=status)


def _json_success(data=None, message='OK', status=200):
    """Helper to return a standardized JSON success response."""
    payload = {'success': True, 'message': message}
    if data is not None:
        payload['data'] = data
    return JsonResponse(payload, status=status)


@login_required
@require_POST
def api_transfer_initiate(request):
    """POST /api/transfers/initiate/

    Create a new transfer request.

    Body (JSON or form-encoded):
        player_id: int (required)
        transfer_type: str ('permanent', 'loan', 'free_agent') — default 'permanent'
        fee: number — default 0
        loan_end_date: str 'YYYY-MM-DD' (required if type is 'loan')

    Returns:
        201: { success: true, data: <transfer_request> }
        400: { success: false, error: <message> }
    """
    # Parse body (support JSON or form POST)
    if request.content_type and 'json' in request.content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return _json_error('Invalid JSON body.')
    else:
        body = request.POST.dict()

    user_team = getattr(request.user, 'team', None)
    if not user_team:
        return _json_error('Only team captains can initiate transfers.', 403)

    try:
        validated = validate_initiate_payload(body)
    except ValueError as e:
        return _json_error(str(e))

    player = Player.objects.filter(pk=validated['player_id']).select_related('team').first()
    if not player:
        return _json_error(f"Player with id {validated['player_id']} not found.", 404)

    window = TransferWindow.objects.filter(is_active=True).first()

    try:
        transfer_request = TransferService.initiate_transfer(
            player=player,
            from_team=player.team,
            to_team=user_team,
            requested_by=request.user,
            window=window,
            transfer_type=validated['transfer_type'],
            fee=validated['fee'],
            loan_end_date=validated['loan_end_date'],
        )
        return _json_success(
            data=serialize_transfer_request(transfer_request),
            message=f'Transfer request for {player.name} created.',
            status=201,
        )
    except TransferError as e:
        return _json_error(str(e))


@login_required
@require_POST
def api_transfer_approve(request, pk):
    """POST /api/transfers/<id>/approve/

    Approve a transfer request (role-aware).

    Returns:
        200: { success: true, message: <result> }
        400: { success: false, error: <message> }
    """
    transfer = TransferRequest.objects.select_related(
        'player', 'from_team', 'to_team', 'window'
    ).filter(pk=pk).first()

    if not transfer:
        return _json_error('Transfer request not found.', 404)

    try:
        result = TransferService.process_approval(
            transfer_request=transfer,
            user=request.user,
            action='approve',
        )
        return _json_success(
            data=serialize_transfer_request(
                TransferRequest.objects.select_related(
                    'player', 'from_team', 'to_team', 'window'
                ).get(pk=pk)
            ),
            message=result,
        )
    except TransferError as e:
        return _json_error(str(e))


@login_required
@require_POST
def api_transfer_reject(request, pk):
    """POST /api/transfers/<id>/reject/

    Reject a transfer request.

    Body (optional):
        reason: str — rejection reason text.

    Returns:
        200: { success: true, message: <result> }
        400: { success: false, error: <message> }
    """
    transfer = TransferRequest.objects.select_related(
        'player', 'from_team', 'to_team', 'window'
    ).filter(pk=pk).first()

    if not transfer:
        return _json_error('Transfer request not found.', 404)

    # Parse reason
    if request.content_type and 'json' in request.content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            body = {}
    else:
        body = request.POST.dict()

    reason = body.get('reason', '')

    try:
        result = TransferService.process_approval(
            transfer_request=transfer,
            user=request.user,
            action='reject',
            reason=reason,
        )
        return _json_success(message=result)
    except TransferError as e:
        return _json_error(str(e))


@login_required
@require_GET
def api_transfer_pending(request):
    """GET /api/transfers/pending/

    List pending transfer requests filtered by the requesting user's role.

    - Team captains: see their incoming (as selling club) pending transfers.
    - Admins: see all transfers awaiting admin review (SELLING_APPROVED).

    Query params:
        status: filter by status (optional, default shows active only)

    Returns:
        200: { success: true, data: [<transfer_request>, ...] }
    """
    user_team = getattr(request.user, 'team', None)
    is_admin = getattr(request.user, 'is_admin_user', False)

    qs = TransferRequest.objects.select_related(
        'player', 'player__team', 'from_team', 'to_team', 'window',
    ).order_by('-created_at')

    status_filter = request.GET.get('status')

    if is_admin:
        # Admins see transfers awaiting their review
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        else:
            qs = qs.filter(status='SELLING_APPROVED')
    elif user_team:
        # Captains see their team's pending incoming transfers
        if status_filter:
            qs = qs.filter(from_team=user_team, status=status_filter.upper())
        else:
            qs = qs.filter(
                from_team=user_team,
                status__in=['PENDING', 'SELLING_APPROVED'],
            )
    else:
        return _json_success(data=[], message='No team associated.')

    transfers = [serialize_transfer_request(tr) for tr in qs[:50]]
    return _json_success(data=transfers)


@login_required
@require_GET
def api_transfer_window_status(request):
    """GET /api/transfers/window/

    Return the current transfer window status.

    Returns:
        200: { success: true, data: <window> | null }
    """
    window = TransferWindow.objects.filter(is_active=True).first()
    return _json_success(
        data=serialize_transfer_window(window),
        message='Open' if (window and window.is_open) else 'Closed',
    )

