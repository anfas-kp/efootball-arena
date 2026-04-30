from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Team, Player
from .forms import TeamForm, PlayerForm


@login_required
def register_team(request):
    """Register a new team."""
    # Check if user already has a team
    if hasattr(request.user, 'team'):
        messages.warning(request, 'You already have a registered team.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user
            team.save()
            messages.success(request, '🎉 Team registered successfully! Awaiting admin verification.')
            return redirect('teams:my_team')
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

    # Get tournament applications for this team
    applications = team.tournament_applications.select_related('tournament', 'assigned_league').all()

    return render(request, 'teams/my_team.html', {
        'team': team,
        'players': players,
        'applications': applications,
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

    if team.player_count >= 20:
        messages.warning(request, 'Maximum roster size (20 players) reached.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.team = team
            player.save()
            messages.success(request, f'✅ {player.name} added to the roster!')
            return redirect('teams:my_team')
    else:
        form = PlayerForm()

    return render(request, 'teams/add_player.html', {'form': form, 'team': team})


@login_required
def edit_player(request, pk):
    """Edit a player."""
    player = get_object_or_404(Player, pk=pk, team__captain=request.user)

    # Roster lock check
    if player.team.is_roster_locked:
        messages.warning(request, '🔒 Roster is locked — cannot edit players during an active tournament.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ {player.name} updated!')
            return redirect('teams:my_team')
    else:
        form = PlayerForm(instance=player)

    return render(request, 'teams/edit_player.html', {'form': form, 'player': player})


@login_required
def delete_player(request, pk):
    """Remove a player from roster."""
    player = get_object_or_404(Player, pk=pk, team__captain=request.user)

    # Roster lock check
    if player.team.is_roster_locked:
        messages.warning(request, '🔒 Roster is locked — cannot remove players during an active tournament.')
        return redirect('teams:my_team')

    if request.method == 'POST':
        name = player.name
        player.delete()
        messages.success(request, f'{name} removed from roster.')
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
