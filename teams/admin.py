from django.contrib import admin
from .models import Team, Player


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'captain', 'platform', 'game', 'status', 'player_count', 'created_at')
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
    list_display = ('name', 'team', 'gaming_id', 'position', 'jersey_number', 'is_active')
    list_filter = ('team', 'position', 'is_active')
    search_fields = ('name', 'gaming_id')
