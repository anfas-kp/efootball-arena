import random

class SeedingEngine:
    @staticmethod
    def seed_random(teams):
        teams_list = list(teams)
        random.shuffle(teams_list)
        return teams_list
