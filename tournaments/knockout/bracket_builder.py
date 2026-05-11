import random
from .bye_balancer import ByeBalancer
from .progression_engine import ProgressionEngine
from tournaments.models import Fixture

class BracketBuilder:
    @staticmethod
    def generate(league):
        """
        Generates a tight bracket with a preliminary round if necessary.
        """
        teams = list(league.teams.all())
        num_teams = len(teams)
        if num_teams < 2: return
        
        # Delete existing
        league.fixtures.all().delete()
        random.shuffle(teams)

        # 1. Determine Structure
        # For 9 teams, base_power=8, play_ins=1
        base_power, play_ins = ByeBalancer.get_target_structure(num_teams)
        
        matchday_offset = 1
        
        # 2. Create Preliminary Round (if any)
        prelim_fixtures = []
        if play_ins > 0:
            # Take teams from the end to play in
            teams_for_prelim = teams[base_power - play_ins:]
            remaining_teams = teams[:base_power - play_ins]
            
            for i in range(play_ins):
                t1 = teams_for_prelim[i*2]
                t2 = teams_for_prelim[i*2 + 1]
                
                fix = Fixture.objects.create(
                    league=league,
                    round_type='preliminary',
                    bracket_index=i,
                    matchday=matchday_offset,
                    home_team=t1,
                    away_team=t2
                )
                prelim_fixtures.append(fix)
                
                if league.knockout_legs == 2:
                    Fixture.objects.create(
                        league=league,
                        round_type='preliminary',
                        bracket_index=i,
                        matchday=matchday_offset + 1,
                        home_team=t2,
                        away_team=t1
                    )
            
            matchday_offset += 2 if league.knockout_legs == 2 else 1
        else:
            remaining_teams = teams

        # 3. Create Main Bracket (from Quarter Finals or whatever base_power is)
        rounds_data = {}
        current_n = base_power
        
        while current_n >= 2:
            round_type = BracketBuilder.get_round_name(current_n)
            num_matches = current_n // 2
            fixtures_in_round = []
            
            for i in range(num_matches):
                fix = Fixture.objects.create(
                    league=league,
                    round_type=round_type,
                    bracket_index=i,
                    matchday=matchday_offset
                )
                fixtures_in_round.append(fix)
                
                if league.knockout_legs == 2 and current_n > 2:
                    Fixture.objects.create(
                        league=league,
                        round_type=round_type,
                        bracket_index=i,
                        matchday=matchday_offset + 1
                    )
            
            rounds_data[current_n] = fixtures_in_round
            matchday_offset += 2 if (league.knockout_legs == 2 and current_n > 2) else 1
            current_n //= 2

        # 4. Link Preliminary to First Main Round
        first_main_round = rounds_data[base_power]
        for i, p_fix in enumerate(prelim_fixtures):
            # Play-ins usually fill the "bottom" slots of the first round
            target_fix = first_main_round[(base_power // 2) - 1 - i]
            p_fix.next_fixture = target_fix
            p_fix.save()
            
            # Link leg 2
            p_leg2 = Fixture.objects.filter(league=league, round_type='preliminary', bracket_index=p_fix.bracket_index, matchday=p_fix.matchday+1).first()
            if p_leg2:
                p_leg2.next_fixture = target_fix
                p_leg2.save()

        # 5. Link Main Rounds
        current_n = base_power
        while current_n > 2:
            curr_fixes = rounds_data[current_n]
            next_fixes = rounds_data[current_n // 2]
            for i, fix in enumerate(curr_fixes):
                next_fix = next_fixes[i // 2]
                fix.next_fixture = next_fix
                fix.save()
                
                leg2 = Fixture.objects.filter(league=league, round_type=fix.round_type, bracket_index=fix.bracket_index, matchday=fix.matchday+1).first()
                if leg2:
                    leg2.next_fixture = next_fix
                    leg2.save()
            current_n //= 2

        # 6. Populate First Main Round
        # Some slots are from remaining_teams, some are from Prelim winners (placeholders)
        # We fill from top down
        for i in range(base_power):
            round_idx = i // 2
            is_away = (i % 2 != 0)
            target_fix = first_main_round[round_idx]
            
            # Is this slot reserved for a prelim winner?
            # Prelims were linked to the bottom-most slots
            is_prelim_slot = False
            for p_fix in prelim_fixtures:
                if p_fix.next_fixture == target_fix:
                    # Check if it's home or away for the target
                    # For simplicity, let's say prelims always feed into the Away slot of their target
                    is_prelim_slot = True
                    break
            
            if not is_prelim_slot:
                if remaining_teams:
                    team = remaining_teams.pop(0)
                    if is_away: target_fix.away_team = team
                    else: target_fix.home_team = team
                    target_fix.save()
                    
                    # Leg 2 reversal
                    leg2 = Fixture.objects.filter(league=league, round_type=target_fix.round_type, bracket_index=target_fix.bracket_index, matchday=target_fix.matchday+1).first()
                    if leg2:
                        if is_away: leg2.home_team = team
                        else: leg2.away_team = team
                        leg2.save()

    @staticmethod
    def get_round_name(n):
        names = {64: 'round_64', 32: 'round_32', 16: 'round_16', 8: 'quarter_final', 4: 'semi_final', 2: 'final'}
        return names.get(n, 'round_of_' + str(n))
