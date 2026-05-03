from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('', views.result_list, name='result_list'),
    path('submit/<int:fixture_pk>/', views.submit_result, name='submit_result'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),
    path('result/<int:pk>/edit/', views.edit_result, name='edit_result'),
    path('result/<int:result_pk>/add-goal/', views.add_goal, name='add_goal'),
    path('result/<int:result_pk>/add-card/', views.add_card, name='add_card'),
    path('result/<int:result_pk>/add-rating/', views.add_rating, name='add_rating'),
    path('result/<int:result_pk>/add-clean-sheet/', views.add_clean_sheet, name='add_clean_sheet'),
    # Admin delete events
    path('goal/<int:goal_pk>/delete/', views.delete_goal, name='delete_goal'),
    path('card/<int:card_pk>/delete/', views.delete_card, name='delete_card'),
    path('rating/<int:rating_pk>/delete/', views.delete_rating, name='delete_rating'),
    path('clean-sheet/<int:cs_pk>/delete/', views.delete_clean_sheet, name='delete_clean_sheet'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    # Admin
    path('admin/verify/', views.admin_verify_results, name='admin_verify'),
    path('admin/approve/<int:pk>/', views.admin_approve_result, name='admin_approve'),
    path('admin/reject/<int:pk>/', views.admin_reject_result, name='admin_reject'),
    path('admin/download-top-scorers/', views.download_top_scorers_pdf, name='download_top_scorers_pdf'),
]
