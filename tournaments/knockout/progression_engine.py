from .aggregate_engine import AggregateEngine
from tournaments.models import Fixture

class ProgressionEngine:
    @staticmethod
    def advance_winner(fixture):
        if not fixture.next_fixture or not fixture.winner:
            return

        next_fix = fixture.next_fixture
        is_even = (fixture.bracket_index % 2 == 0)

        if is_even:
            next_fix.home_team = fixture.winner
        else:
            next_fix.away_team = fixture.winner
        next_fix.save()

        next_leg2 = Fixture.objects.filter(
            league=next_fix.league,
            round_type=next_fix.round_type,
            bracket_index=next_fix.bracket_index,
            matchday=next_fix.matchday + 1
        ).first()

        if next_leg2:
            if is_even: next_leg2.away_team = fixture.winner
            else: next_leg2.home_team = fixture.winner
            next_leg2.save()

    @staticmethod
    def process_result(result):
        fixture = result.fixture
        league = fixture.league
        
        if league.knockout_legs == 1 or fixture.round_type == 'final' or fixture.round_type == 'preliminary':
            if result.winner:
                fixture.winner = result.winner
                fixture.status = 'completed'
                fixture.save()
                ProgressionEngine.advance_winner(fixture)
        else:
            leg2 = Fixture.objects.filter(
                league=league,
                round_type=fixture.round_type,
                bracket_index=fixture.bracket_index
            ).exclude(pk=fixture.pk).first()

            if leg2 and leg2.status == 'completed' and hasattr(leg2, 'result'):
                f1, f2 = (fixture, leg2) if fixture.matchday < leg2.matchday else (leg2, fixture)
                r1, r2 = f1.result, f2.result
                winner, is_tie = AggregateEngine.calculate_aggregate(r1, r2, league.away_goals_rule)
                if is_tie: winner = AggregateEngine.resolve_penalties(r2)
                if winner:
                    f1.winner = winner; f1.save()
                    f2.winner = winner; f2.save()
                    ProgressionEngine.advance_winner(f2)
