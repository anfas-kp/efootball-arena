from django.contrib import admin
from .models import (
    Team, Player, Trophy, TransferWindow, TransferRequest,
    TransferHistory, PlayerRegistration
)


class PlayerInline(admin.TabularInline):
    model = Player
    fk_name = 'team'
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
    list_display = ('name', 'team', 'gaming_id', 'position', 'value', 'is_active', 'is_on_loan', 'is_transfer_listed')
    list_filter = ('team', 'position', 'is_active', 'is_on_loan', 'is_transfer_listed')
    search_fields = ('name', 'gaming_id')
    readonly_fields = ('total_goals', 'total_assists', 'total_red_cards', 'total_yellow_cards', 'total_clean_sheets', 'matches_played', 'avg_rating')

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'team', 'player', 'date_awarded')
    list_filter = ('category',)
    search_fields = ('name', 'team__name', 'player__name')

@admin.register(TransferWindow)
class TransferWindowAdmin(admin.ModelAdmin):
    list_display = ('season', 'start_date', 'end_date', 'is_active', 'is_open', 'max_transfers_per_team', 'created_at')
    list_filter = ('is_active',)
    readonly_fields = ('is_open', 'time_remaining', 'created_at')
    fieldsets = (
        (None, {'fields': ('season', 'start_date', 'end_date', 'is_active')}),
        ('Rules', {'fields': ('allowed_types', 'max_transfers_per_team', 'notes')}),
        ('Computed', {'fields': ('is_open', 'time_remaining', 'created_at')}),
    )
    actions = ['open_windows', 'close_windows']

    @admin.action(description='Open selected transfer windows')
    def open_windows(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Close selected transfer windows')
    def close_windows(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_type', 'transfer_fee', 'status', 'created_at')
    list_filter = ('status', 'transfer_type')
    search_fields = ('player__name', 'from_team__name', 'to_team__name')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    raw_id_fields = ('player', 'from_team', 'to_team', 'requested_by', 'window')

@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = ('player', 'from_team', 'to_team', 'transfer_type', 'transfer_fee', 'transfer_date')
    list_filter = ('transfer_type',)
    search_fields = ('player__name', 'from_team__name', 'to_team__name')
    readonly_fields = ('transfer_date',)

@admin.register(PlayerRegistration)
class PlayerRegistrationAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'league', 'eligible_from', 'is_active', 'matches_played')
    list_filter = ('is_active', 'league')
    search_fields = ('player__name', 'team__name', 'league__name')
    raw_id_fields = ('player', 'team', 'league')
