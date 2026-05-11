from django.db.models import Count, Sum, Q, F
from matches.models import MatchResult
from .models import LeagueStanding, PlayerTournamentStats

def refresh_league_standings(league):
    """
    Calculates standings for a league and saves them to the computed table.
    """
    pts_win = league.tournament.points_win
    pts_draw = league.tournament.points_draw
    pts_loss = league.tournament.points_loss

    teams = league.teams.all()
    
    for team in teams:
        home_res = MatchResult.objects.filter(fixture__league=league, fixture__home_team=team, status='approved').aggregate(
            p=Count('id'), gf=Sum('home_score'), ga=Sum('away_score'),
            w=Count('id', filter=Q(home_score__gt=F('away_score'))),
            d=Count('id', filter=Q(home_score=F('away_score'))),
            l=Count('id', filter=Q(home_score__lt=F('away_score')))
        )
        away_res = MatchResult.objects.filter(fixture__league=league, fixture__away_team=team, status='approved').aggregate(
            p=Count('id'), gf=Sum('away_score'), ga=Sum('home_score'),
            w=Count('id', filter=Q(away_score__gt=F('home_score'))),
            d=Count('id', filter=Q(away_score=F('home_score'))),
            l=Count('id', filter=Q(away_score__lt=F('home_score')))
        )

        played = (home_res['p'] or 0) + (away_res['p'] or 0)
        won = (home_res['w'] or 0) + (away_res['w'] or 0)
        drawn = (home_res['d'] or 0) + (away_res['d'] or 0)
        lost = (home_res['l'] or 0) + (away_res['l'] or 0)
        gf = (home_res['gf'] or 0) + (away_res['gf'] or 0)
        ga = (home_res['ga'] or 0) + (away_res['ga'] or 0)
        
        last_5 = MatchResult.objects.filter(
            Q(fixture__home_team=team) | Q(fixture__away_team=team),
            fixture__league=league, status='approved'
        ).order_by('-fixture__matchday')[:5]
        
        form_str = ""
        for r in reversed(last_5):
            if r.home_score == r.away_score: form_str += 'D'
            elif (r.fixture.home_team == team and r.home_score > r.away_score) or \
                 (r.fixture.away_team == team and r.home_score < r.away_score): form_str += 'W'
            else: form_str += 'L'

        LeagueStanding.objects.update_or_create(
            league=league, team=team,
            defaults={
                'played': played, 'won': won, 'drawn': drawn, 'lost': lost,
                'gf': gf, 'ga': ga, 'gd': gf - ga,
                'points': (won * pts_win) + (drawn * pts_draw) + (lost * pts_loss),
                'form': form_str
            }
        )

def get_league_standings(league):
    """
    Returns standings from the computed table. Triggers refresh if empty.
    """
    standings = LeagueStanding.objects.filter(league=league).select_related('team')
    if not standings.exists() and league.fixtures.filter(status='completed').exists():
        refresh_league_standings(league)
        standings = LeagueStanding.objects.filter(league=league).select_related('team')
    return standings
