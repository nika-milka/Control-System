from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, Defect
from datetime import date, timedelta

User = get_user_model()

class DefectWorkflowIntegrationTest(TestCase):
    """Интеграционный тест 1: Полный цикл создания дефекта - ИСПРАВЛЕННЫЙ"""
    
    def setUp(self):
        self.client = Client()
        
        # Создаем пользователей
        self.engineer = User.objects.create_user(
            username='engineer1',
            password='testpass123',
            role='engineer',
            email='engineer@test.com'
        )
        self.manager = User.objects.create_user(
            username='manager1',
            password='testpass123', 
            role='manager',
            email='manager@test.com'
        )
        
        # Создаем проект
        self.project = Project.objects.create(
            name='Интеграционный тестовый проект',
            description='Проект для интеграционного тестирования',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_complete_defect_workflow(self):
        """Полный цикл: вход → создание дефекта → просмотр → обновление - ИСПРАВЛЕННЫЙ"""
        
        # 1. Вход инженера в систему
        login_success = self.client.login(
            username='engineer1', 
            password='testpass123'
        )
        self.assertTrue(login_success)
        
        # 2. Переход на страницу создания дефекта
        response = self.client.get(reverse('accounts:engineer_defect_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Создание нового дефекта')
        
        # 3. Создание дефекта
        defect_data = {
            'title': 'Интеграционный тестовый дефект',
            'description': 'Дефект создан в интеграционном тесте',
            'project': self.project.id,
            'priority': 'high',
            'assigned_to': self.engineer.id,
            'deadline': (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('accounts:engineer_defect_create'),
            defect_data
        )
        
        # Проверяем редирект на список дефектов (код 302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:engineer_defects_list'))
        
        # 4. Проверяем, что дефект создан в БД
        defect = Defect.objects.filter(title='Интеграционный тестовый дефект').first()
        self.assertIsNotNone(defect)
        self.assertEqual(defect.created_by, self.engineer)
        self.assertEqual(defect.status, 'new')
        
        # 5. Просмотр деталей дефекта
        response = self.client.get(
            reverse('accounts:engineer_defect_detail', args=[defect.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Интеграционный тестовый дефект')
        
        # 6. Обновление статуса дефекта
        response = self.client.post(
            reverse('accounts:engineer_defect_detail', args=[defect.id]),
            {'update_status': '', 'status': 'in_progress'}
        )
        
        # Проверяем редирект обратно на детали дефекта
        self.assertEqual(response.status_code, 302)
        
        # Проверяем обновление статуса
        defect.refresh_from_db()
        self.assertEqual(defect.status, 'in_progress')

class ManagerWorkflowIntegrationTest(TestCase):
    """Интеграционный тест 2: Сценарий работы менеджера - ИСПРАВЛЕННЫЙ"""
    
    def setUp(self):
        self.client = Client()
        
        self.manager = User.objects.create_user(
            username='manager_test',
            password='testpass123',
            role='manager'
        )
        self.engineer = User.objects.create_user(
            username='engineer_test',
            password='testpass123',
            role='engineer'
        )
        
        # Создаем проект для теста
        self.project = Project.objects.create(
            name='Базовый проект',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_manager_project_management_workflow(self):
        """Сценарий: Менеджер создает проект и управляет им - ИСПРАВЛЕННЫЙ"""
        
        # 1. Вход менеджера
        self.client.login(username='manager_test', password='testpass123')
        
        # 2. Создание проекта
        project_data = {
            'name': 'Управленческий тестовый проект',
            'description': 'Проект для тестирования управления',
            'start_date': date.today().strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'manager': self.manager.id
        }
        
        response = self.client.post(
            reverse('accounts:manager_project_create'),
            project_data
        )
        
        # Проверяем редирект на список проектов
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:manager_projects_list'))
        
        # 3. Проверяем создание проекта в БД
        project = Project.objects.filter(name='Управленческий тестовый проект').first()
        self.assertIsNotNone(project)
        
        # 4. Просмотр списка проектов
        response = self.client.get(reverse('accounts:manager_projects_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Управленческий тестовый проект')
        
        # 5. Просмотр деталей проекта
        response = self.client.get(
            reverse('accounts:manager_project_detail', args=[project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.name)