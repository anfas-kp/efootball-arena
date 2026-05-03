def get_league_standings(league):
    fixtures = league.fixtures.filter(status='completed').select_related('result').order_by('matchday')
    tournament = league.tournament

    # Calculate standings
    standings = {}
    for team in league.teams.all():
        standings[team.id] = {
            'team': team,
            'played': 0,
            'won': 0,
            'drawn': 0,
            'lost': 0,
            'gf': 0,
            'ga': 0,
            'gd': 0,
            'points': 0,
            'form': [],  # List of 'W', 'D', 'L'
        }

    for fixture in fixtures:
        if not hasattr(fixture, 'result'):
            continue
        result = fixture.result
        home_id = fixture.home_team_id
        away_id = fixture.away_team_id

        if home_id in standings:
            standings[home_id]['played'] += 1
            standings[home_id]['gf'] += result.home_score
            standings[home_id]['ga'] += result.away_score

        if away_id in standings:
            standings[away_id]['played'] += 1
            standings[away_id]['gf'] += result.away_score
            standings[away_id]['ga'] += result.home_score

        if result.home_score > result.away_score:
            if home_id in standings:
                standings[home_id]['won'] += 1
                standings[home_id]['points'] += tournament.points_win
                standings[home_id]['form'].append('W')
            if away_id in standings:
                standings[away_id]['lost'] += 1
                standings[away_id]['points'] += tournament.points_loss
                standings[away_id]['form'].append('L')
        elif result.home_score < result.away_score:
            if away_id in standings:
                standings[away_id]['won'] += 1
                standings[away_id]['points'] += tournament.points_win
                standings[away_id]['form'].append('W')
            if home_id in standings:
                standings[home_id]['lost'] += 1
                standings[home_id]['points'] += tournament.points_loss
                standings[home_id]['form'].append('L')
        else:
            if home_id in standings:
                standings[home_id]['drawn'] += 1
                standings[home_id]['points'] += tournament.points_draw
                standings[home_id]['form'].append('D')
            if away_id in standings:
                standings[away_id]['drawn'] += 1
                standings[away_id]['points'] += tournament.points_draw
                standings[away_id]['form'].append('D')

    for s in standings.values():
        s['gd'] = s['gf'] - s['ga']
        s['form'] = s['form'][-5:]  # Keep only the last 5 results

    sorted_standings = sorted(
        standings.values(),
        key=lambda x: (-x['points'], -x['gd'], -x['gf'])
    )
    return sorted_standings
