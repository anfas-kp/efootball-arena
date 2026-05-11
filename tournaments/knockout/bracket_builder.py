import random
from django.db import transaction
from .bye_balancer import ByeBalancer
from tournaments.models import Fixture

class BracketBuilder:
    @staticmethod
    @transaction.atomic
    def generate(league, preliminary_teams=None):
        """
        Generates a tight bracket with a preliminary round if necessary.
        Supports automatic BYE balancing and optional manual preliminary selection.
        """
        teams = list(league.teams.all())
        num_teams = len(teams)
        
        if num_teams < 2:
            raise ValueError("At least 2 teams required to build a bracket.")

        # Delete existing fixtures
        league.fixtures.all().delete()

        # 1. Determine Structure
        base_power, play_ins = ByeBalancer.get_target_structure(num_teams)
        
        # 2. Distribute Teams
        if preliminary_teams:
            # Manual selection
            p_teams_list = list(preliminary_teams)
            main_teams = [t for t in teams if t not in p_teams_list]
            random.shuffle(main_teams)
            # We only need exactly play_ins * 2 teams for prelims
            # If user selected more, we'll just use what's needed
            p_teams = p_teams_list[:(play_ins * 2)]
            # Any overflow from manual selection goes back to main_teams
            main_teams.extend(p_teams_list[(play_ins * 2):])
        else:
            # Automatic selection: Last N teams go to preliminary
            random.shuffle(teams)
            p_teams = teams[:(play_ins * 2)]
            main_teams = teams[(play_ins * 2):]

        # 3. Create Main Bracket Structure (from base_power down to 2)
        rounds_data = {}
        current_n = base_power
        
        # We start matchdays at 1 for the main bracket
        # Preliminary round will use matchday 0 (or 1, if we offset others)
        m_offset = 1 if play_ins == 0 else 2 
        
        while current_n >= 2:
            round_type = BracketBuilder.get_round_name(current_n)
            num_matches = current_n // 2
            fixtures_in_round = []
            
            for i in range(num_matches):
                fixture = Fixture.objects.create(
                    league=league,
                    round_type=round_type,
                    bracket_index=i,
                    matchday=m_offset,
                    is_placeholder=(current_n != base_power)
                )
                fixtures_in_round.append(fixture)
                
                # Support 2-leg matches for main rounds
                if league.knockout_legs == 2:
                    Fixture.objects.create(
                        league=league,
                        round_type=round_type,
                        bracket_index=i,
                        matchday=m_offset + 1,
                        is_placeholder=True
                    )

            rounds_data[current_n] = fixtures_in_round
            m_offset += 2 if league.knockout_legs == 2 else 1
            current_n //= 2

        # 4. Link Rounds (Connect winners to the next fixture)
        current_n = base_power
        while current_n > 2:
            curr_fixes = rounds_data[current_n]
            next_fixes = rounds_data[current_n // 2]
            for i, fix in enumerate(curr_fixes):
                next_fix = next_fixes[i // 2]
                fix.next_fixture = next_fix
                fix.save()
                
                # Link leg 2 if exists
                leg2 = Fixture.objects.filter(league=league, round_type=fix.round_type, bracket_index=fix.bracket_index, matchday=fix.matchday+1).first()
                if leg2:
                    leg2.next_fixture = next_fix
                    leg2.save()
            current_n //= 2

        # 5. Handle Preliminary (Play-in) Round
        if play_ins > 0:
            main_round = rounds_data[base_power]
            for i in range(play_ins):
                # We attach play-ins to the bottom-most slots of the first main round
                target_fix = main_round[(base_power // 2) - 1 - i]
                
                p_fix = Fixture.objects.create(
                    league=league,
                    round_type='preliminary',
                    bracket_index=i,
                    matchday=1, # Preliminary happens first
                    next_fixture=target_fix
                )
                
                # Assign teams to Play-in
                if len(p_teams) >= 2:
                    p_fix.home_team = p_teams.pop()
                    p_fix.away_team = p_teams.pop()
                    p_fix.save()
                
                # 2-leg support for Play-in
                if league.knockout_legs == 2:
                    Fixture.objects.create(
                        league=league,
                        round_type='preliminary',
                        bracket_index=i,
                        matchday=2,
                        home_team=p_fix.away_team,
                        away_team=p_fix.home_team,
                        next_fixture=target_fix
                    )

        # 6. Populate Main Round Slots (BYE teams)
        main_round = rounds_data[base_power]
        for fix in main_round:
            # Check if this slot is already being fed by a preliminary match
            # If there's a prelim fixture pointing to this, it will fill the 'Away' slot after completion
            # So the 'Home' slot is available for a BYE team
            has_prelim = Fixture.objects.filter(next_fixture=fix, round_type='preliminary').exists()
            
            if not has_prelim:
                # Slot fully open (2 teams from main_teams)
                if main_teams:
                    fix.home_team = main_teams.pop()
                if main_teams:
                    fix.away_team = main_teams.pop()
                fix.save()
            else:
                # Slot partially open (1 team from main_teams, other from prelim)
                if main_teams:
                    fix.home_team = main_teams.pop()
                    fix.save()

            # Handle 2-leg reversal for populated teams
            leg2 = Fixture.objects.filter(league=league, round_type=fix.round_type, bracket_index=fix.bracket_index, matchday=fix.matchday+1).first()
            if leg2:
                leg2.home_team = fix.away_team
                leg2.away_team = fix.home_team
                leg2.save()

    @staticmethod
    def get_round_name(n):
        names = {
            64: 'round_64', 
            32: 'round_32', 
            16: 'round_16', 
            8: 'quarter_final', 
            4: 'semi_final', 
            2: 'final'
        }
        return names.get(n, f'round_of_{n}')
