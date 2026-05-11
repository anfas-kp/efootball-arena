class AggregateEngine:
    @staticmethod
    def calculate_aggregate(leg1_res, leg2_res, away_goals_enabled=False):
        t1 = leg1_res.fixture.home_team
        t2 = leg1_res.fixture.away_team
        t1_total = leg1_res.home_score + leg2_res.away_score
        t2_total = leg1_res.away_score + leg2_res.home_score
        
        if t1_total > t2_total: return t1, False
        if t2_total > t1_total: return t2, False
        if away_goals_enabled:
            if leg2_res.away_score > leg1_res.away_score: return t1, False
            if leg1_res.away_score > leg2_res.away_score: return t2, False
        return None, True

    @staticmethod
    def resolve_penalties(leg2_res):
        if leg2_res.home_penalties is not None and leg2_res.away_penalties is not None:
            if leg2_res.away_penalties > leg2_res.home_penalties: return leg2_res.fixture.away_team
            if leg2_res.home_penalties > leg2_res.away_penalties: return leg2_res.fixture.home_team
        return None
