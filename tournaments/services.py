import random
import math
from django.db import transaction
from .models import Fixture, League
from teams.models import Team

class KnockoutGenerator:
    """Service to handle automatic knockout fixture generation."""

    ROUND_NAMES = {
        32: 'round_32',
        16: 'round_16',
        8: 'quarter_final',
        4: 'semi_final',
        2: 'final'
    }

    @staticmethod
    @transaction.atomic
    def generate_bracket(league):
        """
        Generates a complete knockout bracket for a league.
        Supports BYEs and multi-leg configurations.
        """
        teams = list(league.teams.all())
        num_teams = len(teams)
        if num_teams < 2:
            return False, "At least 2 teams required."

        # Delete existing fixtures for this league
        league.fixtures.all().delete()

        # 1. Determine the structure (Power of 2)
        # Find the smallest power of 2 greater than or equal to num_teams
        next_power_of_2 = 2**math.ceil(math.log2(num_teams))
        
        # 2. Shuffle teams and add BYEs
        random.shuffle(teams)
        while len(teams) < next_power_of_2:
            teams.append(None)  # Placeholder for BYE

        # 3. Create all fixtures for all rounds
        rounds_data = {}
        current_n = next_power_of_2
        matchday_offset = 1
        
        while current_n >= 2:
            round_type = KnockoutGenerator.ROUND_NAMES.get(current_n, 'preliminary')
            num_matches = current_n // 2
            fixtures_in_round = []
            
            for i in range(num_matches):
                # If it's the final, it's always single leg
                is_two_leg = league.knockout_legs == 2 and current_n > 2
                
                # Create main fixture (Leg 1 or Only Leg)
                fixture = Fixture.objects.create(
                    league=league,
                    round_type=round_type,
                    bracket_index=i,
                    matchday=matchday_offset,
                    is_placeholder=(current_n != next_power_of_2)
                )
                fixtures_in_round.append(fixture)
                
                # If 2-leg, create Leg 2
                if is_two_leg:
                    Fixture.objects.create(
                        league=league,
                        round_type=round_type,
                        bracket_index=i,
                        matchday=matchday_offset + 1,
                        is_placeholder=(current_n != next_power_of_2)
                    )

            rounds_data[current_n] = fixtures_in_round
            matchday_offset += 2 if (league.knockout_legs == 2 and current_n > 2) else 1
            current_n //= 2

        # 4. Link fixtures to their next rounds
        current_n = next_power_of_2
        while current_n > 2:
            current_round = rounds_data[current_n]
            next_round = rounds_data[current_n // 2]
            
            for i, fixture in enumerate(current_round):
                next_index = i // 2
                fixture.next_fixture = next_round[next_index]
                fixture.save()
                
                # Update leg 2 if it exists
                leg2 = Fixture.objects.filter(league=league, round_type=fixture.round_type, bracket_index=fixture.bracket_index, matchday=fixture.matchday+1).first()
                if leg2:
                    leg2.next_fixture = next_round[next_index]
                    leg2.save()
            
            current_n //= 2

        # 5. Populate first round teams
        first_round = rounds_data[next_power_of_2]
        for i in range(0, next_power_of_2, 2):
            t1 = teams[i]
            t2 = teams[i+1]
            fix = first_round[i // 2]
            
            fix.home_team = t1
            fix.away_team = t2
            
            # If t1 or t2 is None, it's a BYE
            if t1 is None or t2 is None:
                # Handle BYE: Winner is the non-None team
                fix.winner = t1 if t1 else t2
                fix.status = 'completed'
                # Advance immediately
                KnockoutGenerator.advance_team(fix)
            
            fix.save()
            
            # Update leg 2 if it exists
            leg2 = Fixture.objects.filter(league=league, round_type=fix.round_type, bracket_index=fix.bracket_index, matchday=fix.matchday+1).first()
            if leg2:
                leg2.home_team = t2 # Reverse for leg 2
                leg2.away_team = t1
                if fix.winner:
                    leg2.status = 'completed'
                    leg2.winner = fix.winner
                leg2.save()

        return True, "Bracket generated successfully."

    @staticmethod
    def advance_team(fixture):
        """Advances the winner of a fixture to the next round slot."""
        if not fixture.next_fixture or not fixture.winner:
            return

        next_fix = fixture.next_fixture
        
        # Determine if this winner goes to home or away slot
        # Based on bracket index: 0, 1 -> next 0 (home, away), 2, 3 -> next 1 (home, away)
        is_even = (fixture.bracket_index % 2 == 0)
        
        if is_even:
            next_fix.home_team = fixture.winner
        else:
            next_fix.away_team = fixture.winner
            
        next_fix.save()
        
        # If next round is 2-leg, update the second leg too
        next_leg2 = Fixture.objects.filter(
            league=next_fix.league, 
            round_type=next_fix.round_type, 
            bracket_index=next_fix.bracket_index, 
            matchday=next_fix.matchday+1
        ).first()
        
        if next_leg2:
            if is_even:
                next_leg2.away_team = fixture.winner # Reverse for leg 2
            else:
                next_leg2.home_team = fixture.winner
            next_leg2.save()

class ProgressionManager:
    """Service to handle team progression logic after match results are approved."""
    
    @staticmethod
    def handle_result_approval(result):
        """
        Called when a MatchResult is approved.
        Checks for completion of a knockout tie and advances the winner.
        """
        fixture = result.fixture
        league = fixture.league
        
        if league.format != 'knockout':
            return

        # 1. Determine if the tie is finished
        is_two_leg = league.knockout_legs == 2 and fixture.round_type != 'final'
        
        if not is_two_leg:
            # Single leg - Winner advances immediately
            fixture.winner = result.winner
            fixture.status = 'completed'
            fixture.save()
            KnockoutGenerator.advance_team(fixture)
        else:
            # Two legs - Check both legs
            other_leg = Fixture.objects.filter(
                league=league, 
                round_type=fixture.round_type, 
                bracket_index=fixture.bracket_index
            ).exclude(pk=fixture.pk).first()
            
            if not other_leg or other_leg.status != 'completed' or not hasattr(other_leg, 'result'):
                # Still waiting for the other leg
                fixture.status = 'completed'
                fixture.save()
                return

            # Both legs are done! Calculate aggregate
            res1 = result if fixture.matchday < other_leg.matchday else other_leg.result
            res2 = result if fixture.matchday > other_leg.matchday else other_leg.result
            
            home_team = res1.fixture.home_team
            away_team = res1.fixture.away_team
            
            # Agg score from perspective of Team 1 (res1.home_team)
            t1_score = res1.home_score + res2.away_score
            t2_score = res1.away_score + res2.home_score
            
            winner = None
            if t1_score > t2_score:
                winner = home_team
            elif t2_score > t1_score:
                winner = away_team
            else:
                # Aggregate draw! Check away goals if enabled
                if league.away_goals_rule:
                    t1_away_goals = res2.away_score
                    t2_away_goals = res1.away_score
                    if t1_away_goals > t2_away_goals:
                        winner = home_team
                    elif t2_away_goals > t1_away_goals:
                        winner = away_team
                
                # If still draw (or no away goals rule), check penalties (from res2)
                if not winner:
                    if res2.home_penalties is not None and res2.away_penalties is not None:
                        # res2 home is away_team, res2 away is home_team
                        if res2.away_penalties > res2.home_penalties:
                            winner = home_team
                        elif res2.home_penalties > res2.away_penalties:
                            winner = away_team
            
            if winner:
                fixture.winner = winner
                fixture.status = 'completed'
                fixture.save()
                other_leg.winner = winner
                other_leg.status = 'completed'
                other_leg.save()
                KnockoutGenerator.advance_team(fixture)
