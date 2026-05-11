import io
from celery import shared_task
from PIL import Image
from django.core.files.base import ContentFile
from django.apps import apps

@shared_task(bind=True, max_retries=3)
def optimize_team_logo(self, team_id):
    """Background task to optimize team logo to WebP."""
    Team = apps.get_model('teams', 'Team')
    try:
        team = Team.objects.get(pk=team_id)
        if not team.logo or team.logo.name.lower().endswith('.webp'):
            return "Already optimized or no logo."

        # Open image from storage
        img_data = team.logo.read()
        img = Image.open(io.BytesIO(img_data))

        if img.format != 'WEBP':
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='WebP', quality=85)
            output.seek(0)
            
            filename = team.logo.name.rsplit('.', 1)[0] + '.webp'
            team.logo.save(filename, ContentFile(output.read()), save=False)
            team.save(update_fields=['logo'])
            return f"Logo optimized for team {team.name}"
            
    except Exception as e:
        # Retry on network issues (like 502)
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def optimize_player_photo(self, player_id):
    """Background task to optimize player photo to WebP."""
    Player = apps.get_model('teams', 'Player')
    try:
        player = Player.objects.get(pk=player_id)
        if not player.photo or player.photo.name.lower().endswith('.webp'):
            return "Already optimized or no photo."

        img_data = player.photo.read()
        img = Image.open(io.BytesIO(img_data))

        if img.format != 'WEBP':
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='WebP', quality=85)
            output.seek(0)
            
            filename = player.photo.name.rsplit('.', 1)[0] + '.webp'
            player.photo.save(filename, ContentFile(output.read()), save=False)
            player.save(update_fields=['photo'])
            return f"Photo optimized for player {player.name}"
            
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
