from .knockout import BracketBuilder, ProgressionEngine

class KnockoutGenerator:
    """Proxy service for knockout fixture generation."""

    @staticmethod
    def generate_bracket(league, preliminary_teams=None):
        """
        Generates a tight bracket using the new modular engine.
        Supports preliminary rounds and manual team selection.
        """
        try:
            BracketBuilder.generate(league, preliminary_teams=preliminary_teams)
            return True, "Bracket generated successfully using the Advanced Modular Engine."
        except Exception as e:
            import logging
            logging.error(f"Error in BracketBuilder: {e}")
            return False, f"Failed to generate bracket: {str(e)}"

class ProgressionManager:
    """Proxy service for team progression logic."""
    
    @staticmethod
    def handle_result_approval(result):
        """
        Delegates progression logic to the ProgressionEngine.
        """
        if result.fixture.league.format == 'knockout':
            ProgressionEngine.process_result(result)
