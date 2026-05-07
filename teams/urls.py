from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    path('register/', views.register_team, name='register_team'),
    path('my-team/', views.my_team, name='my_team'),
    path('players/add/', views.add_player, name='add_player'),
    path('players/<int:pk>/edit/', views.edit_player, name='edit_player'),
    path('players/<int:pk>/delete/', views.delete_player, name='delete_player'),
    path('', views.team_list, name='team_list'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('player/<int:pk>/card/', views.player_card, name='player_card'),
    # Admin
    path('admin/verify/', views.admin_verify_teams, name='admin_verify'),
    path('admin/approve/<int:pk>/', views.admin_approve_team, name='admin_approve'),
    path('admin/reject/<int:pk>/', views.admin_reject_team, name='admin_reject'),
    path('admin/<int:pk>/download-roster/', views.download_team_roster_pdf, name='download_team_roster_pdf'),
    path('admin/team/<int:team_pk>/add-player/', views.admin_add_player, name='admin_add_player'),
    
    # Transfers
    path('transfers/', views.transfer_hub, name='transfer_hub'),
    path('transfers/request/<int:player_id>/', views.request_transfer, name='request_transfer'),
    path('transfers/action/<int:request_id>/<str:action>/', views.transfer_action, name='transfer_action'),
    path('admin/transfer-window/toggle/', views.admin_toggle_transfer_window, name='admin_toggle_transfer_window'),
    
    # API
    path('api/notifications/', views.api_notifications, name='api_notifications'),
]
