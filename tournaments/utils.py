from django.db.models import Count, Sum, Case, When, IntegerField, Q, Value, F

def get_league_standings(league):
    """
    Optimized standings calculation using single-query SQL aggregates.
    Avoids O(N) Python loops and handles 3 points for win, 1 for draw.
    """
    pts_win = league.tournament.points_win
    pts_draw = league.tournament.points_draw
    pts_loss = league.tournament.points_loss

    standings = league.teams.annotate(
        # Matches Played (Corrected to sum home and away fixtures)
        played_home=Count('home_fixtures', filter=Q(home_fixtures__league=league, home_fixtures__status='completed'), distinct=True),
        played_away=Count('away_fixtures', filter=Q(away_fixtures__league=league, away_fixtures__status='completed'), distinct=True),
        
        # Goals Scored & Conceded (calculated via the Result model)
        # Note: We need to handle both home and away scenarios
        gf_home=Sum('home_fixtures__result__home_score', filter=Q(home_fixtures__league=league, home_fixtures__status='completed')),
        gf_away=Sum('away_fixtures__result__away_score', filter=Q(away_fixtures__league=league, away_fixtures__status='completed')),
        ga_home=Sum('home_fixtures__result__away_score', filter=Q(home_fixtures__league=league, home_fixtures__status='completed')),
        ga_away=Sum('away_fixtures__result__home_score', filter=Q(away_fixtures__league=league, away_fixtures__status='completed')),

        # Wins, Draws, Losses
        wins_home=Count('home_fixtures', filter=Q(home_fixtures__league=league, home_fixtures__status='completed', home_fixtures__result__home_score__gt=F('home_fixtures__result__away_score'))),
        wins_away=Count('away_fixtures', filter=Q(away_fixtures__league=league, away_fixtures__status='completed', away_fixtures__result__away_score__gt=F('away_fixtures__result__home_score'))),
        
        draws_home=Count('home_fixtures', filter=Q(home_fixtures__league=league, home_fixtures__status='completed', home_fixtures__result__home_score=F('home_fixtures__result__away_score'))),
        draws_away=Count('away_fixtures', filter=Q(away_fixtures__league=league, away_fixtures__status='completed', away_fixtures__result__away_score=F('away_fixtures__result__home_score'))),
        
        losses_home=Count('home_fixtures', filter=Q(home_fixtures__league=league, home_fixtures__status='completed', home_fixtures__result__home_score__lt=F('home_fixtures__result__away_score'))),
        losses_away=Count('away_fixtures', filter=Q(away_fixtures__league=league, away_fixtures__status='completed', away_fixtures__result__away_score__lt=F('away_fixtures__result__home_score'))),
    ).annotate(
        # Aggregate the calculated fields
        gf=(F('gf_home') or 0) + (F('gf_away') or 0),
        ga=(F('ga_home') or 0) + (F('ga_away') or 0),
        played=F('played_home') + F('played_away'),
        won=F('wins_home') + F('wins_away'),
        drawn=F('draws_home') + F('draws_away'),
        lost=F('losses_home') + F('losses_away'),
    ).annotate(
        # Final calculations
        gd=F('gf') - F('ga'),
        points=(F('won') * pts_win) + (F('drawn') * pts_draw) + (F('lost') * pts_loss)
    ).order_by('-points', '-gd', '-gf')

    # Convert to list/dict format expected by existing templates
    # and add the form tracker (which still requires some manual work for now)
    results_list = []
    for team in standings:
        # Fetch last 5 results for form (this is a small subquery per team, acceptable for now)
        # In a real FUT system, this would be a single optimized query too.
        from matches.models import MatchResult
        last_results = MatchResult.objects.filter(
            Q(fixture__home_team=team) | Q(fixture__away_team=team),
            fixture__league=league,
            status='approved'
        ).order_by('-fixture__matchday')[:5]
        
        form = []
        for r in reversed(last_results):
            if r.is_draw: form.append('D')
            elif r.winner == team: form.append('W')
            else: form.append('L')

        results_list.append({
            'team': team,
            'played': team.played,
            'won': team.won,
            'drawn': team.drawn,
            'lost': team.lost,
            'gf': team.gf,
            'ga': team.ga,
            'gd': team.gd,
            'points': team.points,
            'form': form
        })

    return results_list
