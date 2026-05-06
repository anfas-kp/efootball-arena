import logging
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from matches.models import MatchResult

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes old screenshots from verified match results to save storage space (ignores player/team photos).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Number of days after verification to delete screenshots (default: 2)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Only target APPROVED matches that were verified MORE than X days ago
        results = MatchResult.objects.filter(
            status='approved',
            verified_at__lte=cutoff_date
        )
        
        count_match = 0
        count_goal = 0
        count_card = 0

        for result in results:
            # 1. Delete Main Match Screenshot
            if result.screenshot:
                result.screenshot.delete(save=True)
                count_match += 1
            
            # 2. Delete Goal Screenshots
            for goal in result.goals.all():
                if goal.screenshot:
                    goal.screenshot.delete(save=True)
                    count_goal += 1
                    
            # 3. Delete Card Screenshots
            for card in result.cards.all():
                if card.screenshot:
                    card.screenshot.delete(save=True)
                    count_card += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Successfully deleted old screenshots (older than {days} days since admin approval):\n"
            f" - {count_match} Match Result screenshots deleted\n"
            f" - {count_goal} Goal screenshots deleted\n"
            f" - {count_card} Disciplinary Card screenshots deleted\n"
            f"NOTE: Team logos and Player profile photos were safely ignored."
        ))
