import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Sum, Max, Q
from django.utils.text import slugify
from django.http import HttpResponse, JsonResponse
import random
import string
from .models import Team, Player, Trophy, TransferWindow, TransferRequest, TransferHistory
from .forms import TeamForm, PlayerForm

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
    else:
        player = get_object_or_404(Player, pk=pk, team__captain=request.user)

    # Roster lock check (Admins can bypass lock)
    if player.team.is_roster_locked and not request.user.is_admin_user:
        messages.warning(request, '🔒 Roster is locked — cannot edit players during an active tournament.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ {player.name} updated!')
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('teams:my_team')
    else:
        form = PlayerForm(instance=player)

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
            messages.success(request, f'✅ {player.name} added to {team.name} roster!')
            return redirect('teams:admin_verify')
    else:
        form = PlayerForm()

    return render(request, 'teams/add_player.html', {
        'form': form, 
        'team': team,
        'is_admin': True
    })

# ===== Transfer System Views =====

@login_required
def transfer_hub(request):
    """Transfer Market Dashboard"""
    window = TransferWindow.objects.filter(is_active=True).first()
    
    # All players
    players = Player.objects.filter(is_active=True).select_related('team')
    
    incoming_requests = []
    outgoing_requests = []
    user_team = getattr(request.user, 'team', None)
    
    if user_team:
        incoming_requests = user_team.incoming_transfers.all()
        outgoing_requests = user_team.outgoing_transfers.all()
        
    admin_pending = TransferRequest.objects.filter(status='CURRENT_CAPTAIN_APPROVED') if request.user.is_admin_user else []
        
    return render(request, 'teams/transfer_hub.html', {
        'window': window,
        'players': players,
        'user_team': user_team,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'admin_pending': admin_pending,
    })

@login_required
def request_transfer(request, player_id):
    """Initiate a transfer request."""
    if request.method != 'POST':
        return redirect('teams:transfer_hub')
        
    window = TransferWindow.objects.filter(is_active=True).first()
    if not window:
        messages.error(request, 'Transfer window is closed.')
        return redirect('teams:transfer_hub')
        
    user_team = getattr(request.user, 'team', None)
    if not user_team:
        messages.error(request, 'Only team captains can request transfers.')
        return redirect('teams:transfer_hub')
        
    player = get_object_or_404(Player, pk=player_id)
    if player.team == user_team:
        messages.error(request, 'Player is already on your team.')
        return redirect('teams:transfer_hub')
        
    fee = request.POST.get('fee', 0)
    
    # Check for active request
    if TransferRequest.objects.filter(player=player, to_team=user_team, status__in=['PENDING', 'CURRENT_CAPTAIN_APPROVED']).exists():
        messages.warning(request, 'You already have an active request for this player.')
        return redirect('teams:transfer_hub')
        
    TransferRequest.objects.create(
        player=player,
        from_team=player.team,
        to_team=user_team,
        requested_by=request.user,
        transfer_fee=fee,
        new_captain_approved=True
    )
    
    messages.success(request, f'Transfer request sent for {player.name}!')
    return redirect('teams:transfer_hub')

@login_required
def transfer_action(request, request_id, action):
    """Approve or reject transfer."""
    transfer = get_object_or_404(TransferRequest, pk=request_id)
    user_team = getattr(request.user, 'team', None)
    
    if action == 'reject':
        if request.user.is_admin_user or user_team == transfer.from_team or user_team == transfer.to_team:
            transfer.status = 'REJECTED'
            transfer.save()
            messages.info(request, 'Transfer request rejected.')
        return redirect('teams:transfer_hub')
        
    if action == 'approve':
        if user_team == transfer.from_team and transfer.status == 'PENDING':
            transfer.current_captain_approved = True
            transfer.status = 'CURRENT_CAPTAIN_APPROVED'
            transfer.save()
            messages.success(request, 'You approved the transfer. Awaiting Admin final approval.')
            
        elif request.user.is_admin_user and transfer.status == 'CURRENT_CAPTAIN_APPROVED':
            buyer = transfer.to_team
            seller = transfer.from_team
            fee = transfer.transfer_fee
            
            buyer.budget -= fee
            seller.budget += fee
            buyer.save()
            seller.save()
            
            player = transfer.player
            player.team = buyer
            player.save()
            
            transfer.admin_approved = True
            transfer.status = 'COMPLETED'
            transfer.save()
            
            TransferHistory.objects.create(player=player, from_team=seller, to_team=buyer, transfer_fee=fee)
            messages.success(request, f'Transfer of {player.name} completed successfully.')
            
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
