from django.db.models import Count, Sum, Q, F
from matches.models import MatchResult

def get_league_standings(league):
    """
    Calculates standings for a league.
    Uses a robust approach to avoid Cartesian product issues in single-query aggregates.
    Strictly counts only 'approved' match results.
    """
    pts_win = league.tournament.points_win
    pts_draw = league.tournament.points_draw
    pts_loss = league.tournament.points_loss

    teams = league.teams.all()
    results_list = []

    for team in teams:
        # Home Stats (Approved results only)
        home_results = MatchResult.objects.filter(
            fixture__league=league,
            fixture__home_team=team,
            status='approved'
        ).aggregate(
            played=Count('id'),
            gf=Sum('home_score'),
            ga=Sum('away_score'),
            wins=Count('id', filter=Q(home_score__gt=F('away_score'))),
            draws=Count('id', filter=Q(home_score=F('away_score'))),
            losses=Count('id', filter=Q(home_score__lt=F('away_score')))
        )

        # Away Stats (Approved results only)
        away_results = MatchResult.objects.filter(
            fixture__league=league,
            fixture__away_team=team,
            status='approved'
        ).aggregate(
            played=Count('id'),
            gf=Sum('away_score'),
            ga=Sum('home_score'),
            wins=Count('id', filter=Q(away_score__gt=F('home_score'))),
            draws=Count('id', filter=Q(away_score=F('home_score'))),
            losses=Count('id', filter=Q(away_score__lt=F('home_score')))
        )

        # Combine
        played = (home_results['played'] or 0) + (away_results['played'] or 0)
        won = (home_results['wins'] or 0) + (away_results['wins'] or 0)
        drawn = (home_results['draws'] or 0) + (away_results['draws'] or 0)
        lost = (home_results['losses'] or 0) + (away_results['losses'] or 0)
        gf = (home_results['gf'] or 0) + (away_results['gf'] or 0)
        ga = (home_results['ga'] or 0) + (away_results['ga'] or 0)
        gd = gf - ga
        points = (won * pts_win) + (drawn * pts_draw) + (lost * pts_loss)

        # Fetch last 5 results for form (Approved only)
        last_results = MatchResult.objects.filter(
            Q(fixture__home_team=team) | Q(fixture__away_team=team),
            fixture__league=league,
            status='approved'
        ).order_by('-fixture__matchday')[:5]
        
        form = []
        for r in reversed(last_results):
            if r.home_score == r.away_score: 
                form.append('D')
            elif (r.fixture.home_team == team and r.home_score > r.away_score) or \
                 (r.fixture.away_team == team and r.home_score < r.away_score):
                # Note: r.winner == team logic is safer
                form.append('W')
            else:
                form.append('L')

        results_list.append({
            'team': team,
            'played': played,
            'won': won,
            'drawn': drawn,
            'lost': lost,
            'gf': gf,
            'ga': ga,
            'gd': gd,
            'points': points,
            'form': form
        })

    # Sort by points, then GD, then GF
    results_list.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
    return results_list
