from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Функционал инженера
    path('engineer/defects/', views.engineer_defects_list, name='engineer_defects_list'),
    path('engineer/defects/create/', views.engineer_defect_create, name='engineer_defect_create'),
    path('engineer/defects/<int:defect_id>/', views.engineer_defect_detail, name='engineer_defect_detail'),
    path('engineer/defects/<int:defect_id>/update/', views.engineer_defect_update, name='engineer_defect_update'),
    path('engineer/stats/', views.engineer_my_defects_stats, name='engineer_stats'),
    
    # Примеры защищенных страниц для разных ролей
    path('engineer/defects-protected/', views.engineer_defects_view, name='engineer_defects'),
    path('manager/tasks/', views.manager_tasks_view, name='manager_tasks'),
    path('viewer/reports/', views.viewer_reports_view, name='viewer_reports'),

    # Добавь эти маршруты в urlpatterns
    # Функционал менеджера
    path('manager/tasks/list/', views.manager_tasks_list, name='manager_tasks_list'),
    path('manager/tasks/create/', views.manager_task_create, name='manager_task_create'),
    path('manager/defects/', views.manager_defects_list, name='manager_defects_list'),
    path('manager/defects/<int:defect_id>/assign/', views.manager_defect_assign, name='manager_defect_assign'),
    path('manager/reports/', views.manager_reports, name='manager_reports'),

    # Функционал руководителя
    path('viewer/projects/', views.viewer_projects_overview, name='viewer_projects'),
    path('viewer/defects/', views.viewer_defects_progress, name='viewer_defects'),
    path('viewer/analytics/', views.viewer_analytics, name='viewer_analytics'),

    # Управление проектами менеджера
    path('manager/projects/', views.manager_projects_list, name='manager_projects_list'),
    path('manager/projects/create/', views.manager_project_create, name='manager_project_create'),
    path('manager/projects/<int:project_id>/', views.manager_project_detail, name='manager_project_detail'),
]