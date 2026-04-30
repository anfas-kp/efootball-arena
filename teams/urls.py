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
    # Admin
    path('admin/verify/', views.admin_verify_teams, name='admin_verify'),
    path('admin/approve/<int:pk>/', views.admin_approve_team, name='admin_approve'),
    path('admin/reject/<int:pk>/', views.admin_reject_team, name='admin_reject'),
]
