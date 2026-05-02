from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('', views.tournament_list, name='tournament_list'),
    path('browse/', views.browse_tournaments, name='browse'),
    path('<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('<int:pk>/apply/', views.apply_tournament, name='apply'),
    path('league/<int:pk>/standings/', views.league_standings, name='league_standings'),
    path('league/<int:pk>/fixtures/', views.league_fixtures, name='league_fixtures'),
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/create/', views.admin_create_tournament, name='admin_create'),
    path('admin/<int:pk>/edit/', views.admin_edit_tournament, name='admin_edit'),
    path('admin/<int:tournament_pk>/add-league/', views.admin_add_league, name='admin_add_league'),
    path('admin/<int:tournament_pk>/applications/', views.admin_applications, name='admin_applications'),
    path('admin/application/<int:app_pk>/accept/', views.admin_accept_application, name='admin_accept_app'),
    path('admin/application/<int:app_pk>/reject/', views.admin_reject_application, name='admin_reject_app'),
    path('admin/league/<int:league_pk>/assign-teams/', views.admin_assign_teams, name='admin_assign_teams'),
    path('admin/league/<int:league_pk>/remove-team/<int:team_pk>/', views.admin_remove_team, name='admin_remove_team'),
    path('admin/league/<int:league_pk>/generate-fixtures/', views.admin_generate_fixtures, name='admin_generate_fixtures'),
    path('admin/league/<int:league_pk>/add-fixture/', views.admin_add_fixture, name='admin_add_fixture'),
    path('admin/league/<int:pk>/download-standings/', views.download_league_standings_pdf, name='download_league_standings_pdf'),
    path('admin/league/<int:pk>/download-teams/', views.download_league_teams_pdf, name='download_league_teams_pdf'),
]
