from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, Defect, Task
from datetime import date, timedelta

User = get_user_model()

class UserStoriesTest(TestCase):
    """Тестирование User Stories из технического задания - ИСПРАВЛЕННЫЙ"""
    
    def setUp(self):
        self.client = Client()
        
        # Создаем пользователей всех ролей
        self.engineer = User.objects.create_user(
            username='test_engineer',
            password='testpass123',
            role='engineer'
        )
        self.manager = User.objects.create_user(
            username='test_manager',
            password='testpass123',
            role='manager'
        )
        self.viewer = User.objects.create_user(
            username='test_viewer',
            password='testpass123', 
            role='viewer'
        )
        
        # Создаем тестовый проект
        self.project = Project.objects.create(
            name='Тестовый проект для User Stories',
            description='Проект для тестирования пользовательских сценариев',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_engineer_user_story(self):
        """User Story: Инженер регистрирует дефекты и обновляет информацию - ИСПРАВЛЕННЫЙ"""
        
        # Вход инженера
        self.client.login(username='test_engineer', password='testpass123')
        
        # 1. Регистрация дефекта
        defect_data = {
            'title': 'Обнаружен дефект фундамента',
            'description': 'Трещина в фундаменте на участке А-15',
            'project': self.project.id,
            'priority': 'high',
            'assigned_to': self.engineer.id,
            'deadline': (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('accounts:engineer_defect_create'),
            defect_data
        )
        
        # Проверяем редирект на список дефектов
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:engineer_defects_list'))
        
        # Проверяем запись в БД
        defect = Defect.objects.get(title='Обнаружен дефект фундамента')
        self.assertEqual(defect.created_by, self.engineer)
        self.assertEqual(defect.status, 'new')
        
        # 2. Обновление информации о дефекте
        update_data = {
            'title': 'Обнаружен дефект фундамента (уточнение)',
            'description': 'Трещина в фундаменте на участке А-15, требуется срочный ремонт',
            'status': 'in_progress',
            'priority': 'critical',
            'assigned_to': self.engineer.id,
            'deadline': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('accounts:engineer_defect_update', args=[defect.id]),
            update_data
        )
        
        # Проверяем редирект на детали дефекта
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:engineer_defect_detail', args=[defect.id]))
        
        # Проверяем изменения в БД
        defect.refresh_from_db()
        self.assertEqual(defect.status, 'in_progress')
        self.assertEqual(defect.priority, 'critical')
    
    def test_manager_user_story(self):
        """User Story: Менеджер назначает задачи, контролирует сроки, формирует отчеты - ИСПРАВЛЕННЫЙ"""
        
        self.client.login(username='test_manager', password='testpass123')
        
        # 1. Назначение задачи
        task_data = {
            'title': 'Проверить качество бетонных работ',
            'description': 'Провести выборочную проверку качества бетона на объекте',
            'project': self.project.id,
            'assigned_to': self.engineer.id,
            'deadline': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('accounts:manager_task_create'),
            task_data
        )
        
        # Проверяем редирект на список задач
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:manager_tasks_list'))
        
        # Проверяем создание задачи в БД
        task = Task.objects.get(title='Проверить качество бетонных работ')
        self.assertEqual(task.assigned_to, self.engineer)
        
        # 2. Контроль сроков - проверяем просроченные дефекты
        # Создаем просроченный дефект
        overdue_defect = Defect.objects.create(
            title='Просроченный дефект для контроля',
            description='Дефект для тестирования контроля сроков',
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() - timedelta(days=1),
            status='in_progress'
        )
        
        # Проверяем, что дефект отмечен как просроченный
        self.assertTrue(overdue_defect.is_overdue)
        
        # 3. Формирование отчетов - проверяем доступ к отчетам
        response = self.client.get(reverse('accounts:manager_reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Отчетность')
        
        # Проверяем статистику в отчетах
        self.assertIn('total_defects', response.context)
        self.assertIn('projects_stats', response.context)
    
    def test_viewer_user_story(self):
        """User Story: Руководитель просматривает прогресс и отчетность - ИСПРАВЛЕННЫЙ"""
        
        self.client.login(username='test_viewer', password='testpass123')
        
        # Создаем тестовые данные для отчетов
        Defect.objects.create(
            title='Дефект для отчета 1',
            description='Описание',
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() + timedelta(days=10),
            status='new'
        )
        
        Defect.objects.create(
            title='Дефект для отчета 2',
            description='Описание', 
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() + timedelta(days=15),
            status='closed'
        )
        
        # 1. Просмотр прогресса проектов
        response = self.client.get(reverse('accounts:viewer_projects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Обзор проектов')
        
        # Проверяем, что статистика передается в шаблон
        self.assertIn('projects_with_stats', response.context)
        
        # 2. Просмотр прогресса дефектов
        response = self.client.get(reverse('accounts:viewer_defects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Прогресс по дефектам')
        
        # 3. Просмотр аналитики
        response = self.client.get(reverse('accounts:viewer_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Аналитика и статистика')
        
        # Проверяем наличие данных аналитики
        self.assertIn('defects_by_status', response.context)
        self.assertIn('defects_by_priority', response.context)