from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import League

@login_required
def admin_add_fixture(request, league_pk):
    """Admin manually adds a fixture to a league."""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    league = get_object_or_404(League, pk=league_pk)
    
    if request.method == 'POST':
        from .forms import FixtureForm
        form = FixtureForm(league, request.POST)
        if form.is_valid():
            fixture = form.save(commit=False)
            fixture.league = league
            fixture.save()
            messages.success(request, f'✅ Fixture added to {league.name}.')
            return redirect('tournaments:league_fixtures', pk=league.pk)
    else:
        from .forms import FixtureForm
        form = FixtureForm(league)

    return render(request, 'tournaments/admin_add_fixture.html', {
        'league': league,
        'form': form,
        'tournament': league.tournament,
    })
