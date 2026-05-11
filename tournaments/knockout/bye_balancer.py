import math

class ByeBalancer:
    @staticmethod
    def get_target_structure(n):
        """
        Determines if we should use a full power-of-2 tree or a play-in structure.
        For 9 teams, it returns (8, 1) -> Target 8 teams with 1 play-in match.
        """
        if n <= 2: return 2, 0
        
        # Base power is the nearest power of 2 LESS than or equal to n
        base_power = 2**math.floor(math.log2(n))
        
        # If it's already a power of 2, no play-ins needed
        if base_power == n:
            return base_power, 0
            
        # Number of matches needed to reach base_power
        # Every match reduces the field by 1 team.
        # So we need (n - base_power) matches.
        play_ins = n - base_power
        return base_power, play_ins

    @staticmethod
    def balance_teams(teams):
        """
        Legacy support for full padding if needed.
        """
        num_teams = len(teams)
        next_power = 2**math.ceil(math.log2(num_teams))
        teams_list = list(teams)
        padding_needed = next_power - num_teams
        teams_list.extend([None] * padding_needed)
        return teams_list, next_power
