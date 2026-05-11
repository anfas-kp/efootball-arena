from .aggregate_engine import AggregateEngine
from tournaments.models import Fixture

class ProgressionEngine:
    @staticmethod
    def advance_winner(fixture):
        """
        Moves the winner of a fixture to the next round slot.
        Handles home/away slot assignment based on bracket index.
        """
        if not fixture.next_fixture or not fixture.winner:
            return

        next_fix = fixture.next_fixture
        league = fixture.league
        winner = fixture.winner

        # Logic for slotting:
        # If it's from a preliminary round, it usually fills the AWAY slot 
        # of the bottom matches in the first main round.
        if fixture.round_type == 'preliminary':
            # Preliminary winners always fill the AWAY slot of their target
            next_fix.away_team = winner
        else:
            # Main bracket logic: 0,1 -> next 0 (home, away), etc.
            is_even = (fixture.bracket_index % 2 == 0)
            if is_even:
                next_fix.home_team = winner
            else:
                next_fix.away_team = winner
        
        next_fix.save()

        # Handle 2-leg next rounds (if applicable)
        next_leg2 = Fixture.objects.filter(
            league=league,
            round_type=next_fix.round_type,
            bracket_index=next_fix.bracket_index
        ).exclude(pk=next_fix.pk).first()

        if next_leg2:
            # Next leg 2 has swapped home/away
            if fixture.round_type == 'preliminary':
                next_leg2.home_team = winner
            else:
                is_even = (fixture.bracket_index % 2 == 0)
                if is_even:
                    next_leg2.away_team = winner
                else:
                    next_leg2.home_team = winner
            next_leg2.save()

    @staticmethod
    def process_result(result):
        """
        Orchestrates the completion of a match/tie.
        Calculates aggregate if 2-leg, then triggers advancement.
        """
        fixture = result.fixture
        league = fixture.league
        
        # Determine if this tie (1 or 2 matches) is finished
        is_two_leg = league.knockout_legs == 2 and fixture.round_type != 'final'
        
        if not is_two_leg:
            # Single leg - Winner advances immediately
            if result.winner:
                fixture.winner = result.winner
                fixture.status = 'completed'
                fixture.save()
                ProgressionEngine.advance_winner(fixture)
        else:
            # Two legs - Check both
            leg2 = Fixture.objects.filter(
                league=league,
                round_type=fixture.round_type,
                bracket_index=fixture.bracket_index
            ).exclude(pk=fixture.pk).first()

            if leg2 and leg2.status == 'completed' and hasattr(leg2, 'result'):
                # Both legs done!
                f1, f2 = (fixture, leg2) if fixture.matchday < leg2.matchday else (leg2, fixture)
                r1, r2 = f1.result, f2.result
                
                winner, is_tie = AggregateEngine.calculate_aggregate(r1, r2, league.away_goals_rule)
                if is_tie:
                    winner = AggregateEngine.resolve_penalties(r2)
                
                if winner:
                    f1.winner = winner; f1.save()
                    f2.winner = winner; f2.save()
                    ProgressionEngine.advance_winner(f2)
            else:
                # Still waiting for other leg
                fixture.status = 'completed'
                fixture.save()
