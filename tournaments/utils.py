def get_league_standings(league):
    fixtures = league.fixtures.filter(status='completed')
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
            if away_id in standings:
                standings[away_id]['lost'] += 1
                standings[away_id]['points'] += tournament.points_loss
        elif result.home_score < result.away_score:
            if away_id in standings:
                standings[away_id]['won'] += 1
                standings[away_id]['points'] += tournament.points_win
            if home_id in standings:
                standings[home_id]['lost'] += 1
                standings[home_id]['points'] += tournament.points_loss
        else:
            if home_id in standings:
                standings[home_id]['drawn'] += 1
                standings[home_id]['points'] += tournament.points_draw
            if away_id in standings:
                standings[away_id]['drawn'] += 1
                standings[away_id]['points'] += tournament.points_draw

    for s in standings.values():
        s['gd'] = s['gf'] - s['ga']

    sorted_standings = sorted(
        standings.values(),
        key=lambda x: (-x['points'], -x['gd'], -x['gf'])
    )
    return sorted_standings
