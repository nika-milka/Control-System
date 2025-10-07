from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.template import loader
import logging

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .defect_forms import DefectForm, DefectUpdateForm, DefectCommentForm, DefectAttachmentForm
from .manager_forms import TaskForm, DefectAssignmentForm, ProjectForm
from .decorators import engineer_required, manager_required, viewer_required, log_user_action
from .models import Project, Defect, DefectComment, DefectAttachment, Task, Report

logger = logging.getLogger('accounts')

# Обработчики ошибок
def handler403(request, exception):
    """Обработчик ошибки 403 (Доступ запрещен)"""
    logger.warning(f'Ошибка 403: {exception} - Пользователь: {request.user} - IP: {request.META.get("REMOTE_ADDR")}')
    template = loader.get_template('accounts/403.html')
    return HttpResponseForbidden(template.render({}))

def handler404(request, exception):
    """Обработчик ошибки 404 (Не найдено)"""
    logger.warning(f'Ошибка 404: {request.path} - Пользователь: {request.user} - IP: {request.META.get("REMOTE_ADDR")}')
    template = loader.get_template('accounts/404.html')
    return HttpResponseNotFound(template.render({}))

def handler500(request):
    """Обработчик ошибки 500 (Ошибка сервера)"""
    logger.error(f'Ошибка 500: {request.path} - Пользователь: {request.user} - IP: {request.META.get("REMOTE_ADDR")}')
    template = loader.get_template('accounts/500.html')
    return HttpResponseServerError(template.render({}))

# Основные представления
def home_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'accounts/home.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {user.username}!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@log_user_action("вошел в систему")
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                next_url = request.GET.get('next', 'accounts:dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@log_user_action("вышел из системы")
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('accounts:login')

@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'role_display': user.get_role_display(),
    }
    
    # Разные шаблоны для разных ролей
    if user.is_engineer():
        template = 'accounts/dashboard_engineer.html'
    elif user.is_manager():
        template = 'accounts/dashboard_manager.html'
    else:  # viewer
        template = 'accounts/dashboard_viewer.html'
    
    return render(request, template, context)

# Функционал для инженеров
@engineer_required
def engineer_defects_list(request):
    defects = Defect.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        defects = defects.filter(status=status_filter)
    
    context = {
        'defects': defects,
        'status_choices': Defect.STATUS_CHOICES,
        'current_status': status_filter,
    }
    return render(request, 'accounts/engineer_defects_list.html', context)

@engineer_required
@log_user_action("создал дефект")
def engineer_defect_create(request):
    if request.method == 'POST':
        form = DefectForm(request.POST, request.FILES)
        if form.is_valid():
            defect = form.save(commit=False)
            defect.created_by = request.user
            defect.save()
            messages.success(request, 'Дефект успешно создан!')
            return redirect('accounts:engineer_defects_list')
    else:
        form = DefectForm()
    
    context = {'form': form}
    return render(request, 'accounts/engineer_defect_form.html', context)

@engineer_required
def engineer_defect_detail(request, defect_id):
    defect = get_object_or_404(Defect, id=defect_id, assigned_to=request.user)
    comments = defect.comments.all().order_by('created_at')
    attachments = defect.attachments.all()
    
    comment_form = DefectCommentForm()
    attachment_form = DefectAttachmentForm()
    
    if request.method == 'POST':
        if 'add_comment' in request.POST:
            comment_form = DefectCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.defect = defect
                comment.author = request.user
                comment.save()
                messages.success(request, 'Комментарий добавлен!')
                return redirect('accounts:engineer_defect_detail', defect_id=defect.id)
        
        elif 'add_attachment' in request.POST:
            attachment_form = DefectAttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                attachment = attachment_form.save(commit=False)
                attachment.defect = defect
                attachment.uploaded_by = request.user
                attachment.save()
                messages.success(request, 'Файл загружен!')
                return redirect('accounts:engineer_defect_detail', defect_id=defect.id)
        
        elif 'update_status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in dict(Defect.STATUS_CHOICES):
                defect.status = new_status
                defect.save()
                messages.success(request, f'Статус изменен на "{defect.get_status_display()}"')
                return redirect('accounts:engineer_defect_detail', defect_id=defect.id)
    
    context = {
        'defect': defect,
        'comments': comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
    }
    return render(request, 'accounts/engineer_defect_detail.html', context)

@engineer_required
@log_user_action("обновил дефект")
def engineer_defect_update(request, defect_id):
    defect = get_object_or_404(Defect, id=defect_id, assigned_to=request.user)
    
    if request.method == 'POST':
        form = DefectUpdateForm(request.POST, instance=defect)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дефект успешно обновлен!')
            return redirect('accounts:engineer_defect_detail', defect_id=defect.id)
    else:
        form = DefectUpdateForm(instance=defect)
    
    context = {'form': form, 'defect': defect}
    return render(request, 'accounts/engineer_defect_form.html', context)

@engineer_required
def engineer_my_defects_stats(request):
    defects = Defect.objects.filter(assigned_to=request.user)
    
    # Статистика по статусам
    status_stats = {}
    for status_code, status_name in Defect.STATUS_CHOICES:
        count = defects.filter(status=status_code).count()
        status_stats[status_name] = count
    
    # Статистика по приоритетам
    priority_stats = {}
    for priority_code, priority_name in Defect.PRIORITY_CHOICES:
        count = defects.filter(priority=priority_code).count()
        priority_stats[priority_name] = count
    
    # Просроченные дефекты
    from datetime import date
    overdue_defects = defects.filter(deadline__lt=date.today()).exclude(status__in=['closed', 'cancelled'])
    
    context = {
        'status_stats': status_stats,
        'priority_stats': priority_stats,
        'overdue_defects': overdue_defects,
        'total_defects': defects.count(),
    }
    return render(request, 'accounts/engineer_stats.html', context)

# Функционал менеджера
@manager_required
def manager_projects_list(request):
    projects = Project.objects.all().order_by('-created_at')
    
    # Добавляем статистику для каждого проекта
    projects_with_stats = []
    total_defects_count = 0
    active_defects_count = 0
    completed_defects_count = 0
    
    for project in projects:
        defects = Defect.objects.filter(project=project)
        open_defects = defects.exclude(status__in=['closed', 'cancelled']).count()
        closed_defects = defects.filter(status='closed').count()
        
        total_defects_count += defects.count()
        active_defects_count += open_defects
        completed_defects_count += closed_defects
        
        projects_with_stats.append({
            'project': project,
            'total_defects': defects.count(),
            'open_defects': open_defects,
            'closed_defects': closed_defects,
        })
    
    context = {
        'projects_with_stats': projects_with_stats,
        'total_defects_count': total_defects_count,
        'active_defects_count': active_defects_count,
        'completed_defects_count': completed_defects_count,
    }
    return render(request, 'accounts/manager_projects_list.html', context)

@manager_required
@log_user_action("создал проект")
def manager_project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, 'Проект успешно создан!')
            return redirect('accounts:manager_projects_list')
    else:
        form = ProjectForm()
    
    context = {'form': form}
    return render(request, 'accounts/manager_project_form.html', context)

@manager_required
def manager_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    defects = Defect.objects.filter(project=project)
    tasks = Task.objects.filter(project=project)
    
    # Статистика по проекту
    total_defects = defects.count()
    open_defects = defects.exclude(status__in=['closed', 'cancelled']).count()
    closed_defects = defects.filter(status='closed').count()
    
    context = {
        'project': project,
        'defects': defects,
        'tasks': tasks,
        'total_defects': total_defects,
        'open_defects': open_defects,
        'closed_defects': closed_defects,
        'completion_rate': (closed_defects / total_defects * 100) if total_defects > 0 else 0,
    }
    return render(request, 'accounts/manager_project_detail.html', context)

@manager_required
def manager_tasks_list(request):
    tasks = Task.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    context = {
        'tasks': tasks,
        'status_choices': Task._meta.get_field('status').choices,
        'current_status': status_filter,
    }
    return render(request, 'accounts/manager_tasks_list.html', context)

@manager_required
@log_user_action("создал задачу")
def manager_task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Задача успешно создана!')
            return redirect('accounts:manager_tasks_list')
    else:
        form = TaskForm()
    
    context = {'form': form}
    return render(request, 'accounts/manager_task_form.html', context)

@manager_required
def manager_defects_list(request):
    defects = Defect.objects.all().order_by('-created_at')
    
    # Фильтрация
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    
    if status_filter:
        defects = defects.filter(status=status_filter)
    if priority_filter:
        defects = defects.filter(priority=priority_filter)
    
    context = {
        'defects': defects,
        'status_choices': Defect.STATUS_CHOICES,
        'priority_choices': Defect.PRIORITY_CHOICES,
        'current_status': status_filter,
        'current_priority': priority_filter,
    }
    return render(request, 'accounts/manager_defects_list.html', context)

@manager_required
@log_user_action("назначил дефект")
def manager_defect_assign(request, defect_id):
    defect = get_object_or_404(Defect, id=defect_id)
    
    if request.method == 'POST':
        form = DefectAssignmentForm(request.POST, instance=defect)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дефект успешно назначен!')
            return redirect('accounts:manager_defects_list')
    else:
        form = DefectAssignmentForm(instance=defect)
    
    context = {'form': form, 'defect': defect}
    return render(request, 'accounts/manager_defect_assign.html', context)

@manager_required
def manager_reports(request):
    # Генерация простой статистики
    total_defects = Defect.objects.count()
    open_defects = Defect.objects.exclude(status__in=['closed', 'cancelled']).count()
    closed_defects = Defect.objects.filter(status='closed').count()
    
    # Статистика по проектам
    projects_stats = []
    for project in Project.objects.all():
        project_defects = Defect.objects.filter(project=project)
        projects_stats.append({
            'project': project,
            'total': project_defects.count(),
            'open': project_defects.exclude(status__in=['closed', 'cancelled']).count(),
            'closed': project_defects.filter(status='closed').count(),
        })
    
    context = {
        'total_defects': total_defects,
        'open_defects': open_defects,
        'closed_defects': closed_defects,
        'projects_stats': projects_stats,
    }
    return render(request, 'accounts/manager_reports.html', context)

# Функционал руководителя/заказчика
@viewer_required
def viewer_projects_overview(request):
    projects = Project.objects.all()
    projects_with_stats = []
    
    for project in projects:
        defects = Defect.objects.filter(project=project)
        closed_defects = defects.filter(status='closed').count()
        total_defects = defects.count()
        
        completion_rate = (closed_defects / total_defects * 100) if total_defects > 0 else 0
        
        projects_with_stats.append({
            'project': project,
            'total_defects': total_defects,
            'open_defects': defects.exclude(status__in=['closed', 'cancelled']).count(),
            'closed_defects': closed_defects,
            'completion_rate': completion_rate,
        })
    
    context = {
        'projects_with_stats': projects_with_stats,
    }
    return render(request, 'accounts/viewer_projects_overview.html', context)

@viewer_required
def viewer_defects_progress(request):
    defects = Defect.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        defects = defects.filter(status=status_filter)
    
    # Статистика по статусам
    status_stats = {}
    for status_code, status_name in Defect.STATUS_CHOICES:
        count = defects.filter(status=status_code).count()
        status_stats[status_name] = count
    
    context = {
        'defects': defects[:10],  # Последние 10 дефектов
        'status_stats': status_stats,
        'status_choices': Defect.STATUS_CHOICES,
        'current_status': status_filter,
        'total_defects': defects.count(),
    }
    return render(request, 'accounts/viewer_defects_progress.html', context)

@viewer_required
def viewer_analytics(request):
    # Аналитика по дефектам
    defects_by_status = Defect.objects.values('status').annotate(count=models.Count('id'))
    defects_by_priority = Defect.objects.values('priority').annotate(count=models.Count('id'))
    defects_by_project = Defect.objects.values('project__name').annotate(count=models.Count('id'))
    
    # Просроченные дефекты
    from datetime import date
    overdue_defects = Defect.objects.filter(deadline__lt=date.today()).exclude(status__in=['closed', 'cancelled'])
    
    context = {
        'defects_by_status': list(defects_by_status),
        'defects_by_priority': list(defects_by_priority),
        'defects_by_project': list(defects_by_project),
        'overdue_defects': overdue_defects,
    }
    return render(request, 'accounts/viewer_analytics.html', context)

# Простые заглушки для демонстрации
@engineer_required
def engineer_defects_view(request):
    return render(request, 'accounts/engineer_defects.html')

@manager_required  
def manager_tasks_view(request):
    return render(request, 'accounts/manager_tasks.html')

@viewer_required
def viewer_reports_view(request):
    return render(request, 'accounts/viewer_reports.html')