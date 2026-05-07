from django.contrib import admin
from .models import Team, Player, Trophy, TransferWindow, TransferRequest, TransferHistory


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'captain', 'platform', 'game', 'status', 'budget', 'player_count', 'created_at')
    list_filter = ('status', 'platform', 'game')
    search_fields = ('name', 'captain__username')
    inlines = [PlayerInline]
    actions = ['approve_teams', 'reject_teams']

    @admin.action(description='Approve selected teams')
    def approve_teams(self, request, queryset):
        queryset.update(status='approved')

    @admin.action(description='Reject selected teams')
    def reject_teams(self, request, queryset):
        queryset.update(status='rejected')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'gaming_id', 'position', 'value', 'is_active')
    list_filter = ('team', 'position', 'is_active')
    search_fields = ('name', 'gaming_id')

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'team', 'player', 'date_awarded')
    list_filter = ('category',)
    search_fields = ('name', 'team__name', 'player__name')

@admin.register(TransferWindow)
class TransferWindowAdmin(admin.ModelAdmin):
    list_display = ('season', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)
    actions = ['open_windows', 'close_windows']

    @admin.action(description='Open selected transfer windows')
    def open_windows(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Close selected transfer windows')
    def close_windows(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_fee', 'status', 'created_at')
    list_filter = ('status', 'current_captain_approved', 'new_captain_approved', 'admin_approved')
    search_fields = ('player__name', 'from_team__name', 'to_team__name')
    actions = ['approve_transfers']

    @admin.action(description='Admin Final Approve selected transfers')
    def approve_transfers(self, request, queryset):
        for transfer in queryset:
            if transfer.status == 'NEW_CAPTAIN_APPROVED' or transfer.status == 'PENDING':
                transfer.admin_approved = True
                transfer.status = 'COMPLETED'
                transfer.save()
                
                # Move player
                player = transfer.player
                player.team = transfer.to_team
                player.save()
                
                # Create history
                TransferHistory.objects.create(
                    player=player,
                    from_team=transfer.from_team,
                    to_team=transfer.to_team,
                    transfer_fee=transfer.transfer_fee
                )

@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_fee', 'transfer_date')
    search_fields = ('player__name', 'from_team__name', 'to_team__name')
