from django.contrib import admin
from .models import Tournament, League, Fixture


class LeagueInline(admin.TabularInline):
    model = League
    extra = 0


class FixtureInline(admin.TabularInline):
    model = Fixture
    extra = 0


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('status', 'is_active')
    search_fields = ('name',)
    inlines = [LeagueInline]


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'format', 'max_teams', 'team_count')
    list_filter = ('tournament', 'format')
    filter_horizontal = ('teams',)
    inlines = [FixtureInline]


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'league', 'matchday', 'match_date', 'status')
    list_filter = ('status', 'league', 'matchday')
