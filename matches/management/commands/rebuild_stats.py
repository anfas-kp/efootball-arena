from django.core.management.base import BaseCommand
from django.db.models import Avg
from teams.models import Player


class Command(BaseCommand):
    help = 'Rebuild all player stats (goals, assists, cards, ratings, clean sheets) from actual records.'

    def handle(self, *args, **options):
        players = Player.objects.all()
        total = players.count()

        self.stdout.write(f'Rebuilding stats for {total} players...\n')

        for i, player in enumerate(players, 1):
            player.total_goals = player.goals_scored.filter(result__status='approved').count()
            player.total_assists = player.assists.filter(result__status='approved').count()
            player.total_red_cards = player.cards.filter(card_type='red', result__status='approved').count()
            player.total_yellow_cards = player.cards.filter(card_type='yellow', result__status='approved').count()

            ratings = player.match_ratings.filter(result__status='approved')
            player.avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0

            player.total_clean_sheets = player.clean_sheet_records.filter(
                result__status='approved'
            ).count()

            player.save(update_fields=[
                'total_goals', 'total_assists',
                'total_red_cards', 'total_yellow_cards',
                'avg_rating', 'total_clean_sheets',
            ])

            if i % 50 == 0:
                self.stdout.write(f'  Processed {i}/{total}...')

        self.stdout.write(self.style.SUCCESS(f'✅ Done! Rebuilt stats for {total} players.'))
