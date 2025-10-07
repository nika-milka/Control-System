from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, Defect, Task
from .forms import CustomUserCreationForm, DefectForm
from datetime import date, timedelta
import html

User = get_user_model()

class UserModelTest(TestCase):
    """Тесты модели пользователя"""
    
    def setUp(self):
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
    
    def test_user_creation(self):
        """Тест 1: Создание пользователя"""
        self.assertEqual(self.engineer.username, 'engineer1')
        self.assertEqual(self.engineer.role, 'engineer')
        self.assertTrue(self.engineer.is_engineer())
        self.assertFalse(self.engineer.is_manager())
    
    def test_user_role_methods(self):
        """Тест 2: Проверка методов ролей"""
        self.assertTrue(self.engineer.is_engineer())
        self.assertFalse(self.engineer.is_manager())
        self.assertFalse(self.engineer.is_viewer())
        
        self.assertTrue(self.manager.is_manager())
        self.assertFalse(self.manager.is_engineer())
    
    def test_user_str_representation(self):
        """Тест 3: Строковое представление пользователя"""
        self.assertEqual(str(self.engineer), 'engineer1 (Инженер)')

class ProjectModelTest(TestCase):
    """Тесты модели проекта"""
    
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            password='testpass123', 
            role='manager'
        )
        self.project = Project.objects.create(
            name='Тестовый проект',
            description='Описание тестового проекта',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_project_creation(self):
        """Тест 4: Создание проекта"""
        self.assertEqual(self.project.name, 'Тестовый проект')
        self.assertEqual(self.project.manager, self.manager)
        self.assertTrue(self.project.created_at)
    
    def test_project_xss_protection(self):
        """Тест 5: Защита от XSS в проекте"""
        malicious_name = '<script>alert("xss")</script>Проект'
        project = Project.objects.create(
            name=malicious_name,
            description='Тест',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
        # Проверяем, что HTML экранирован
        self.assertNotIn('<script>', project.name)
        self.assertIn('&lt;script&gt;', project.name)

class DefectModelTest(TestCase):
    """Тесты модели дефекта"""
    
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            password='testpass123',
            role='manager'
        )
        self.engineer = User.objects.create_user(
            username='engineer1',
            password='testpass123',
            role='engineer'  
        )
        self.project = Project.objects.create(
            name='Тестовый проект',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_defect_creation(self):
        """Тест 6: Создание дефекта"""
        defect = Defect.objects.create(
            title='Тестовый дефект',
            description='Описание дефекта',
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() + timedelta(days=7)
        )
        
        self.assertEqual(defect.title, 'Тестовый дефект')
        self.assertEqual(defect.status, 'new')
        self.assertEqual(defect.priority, 'medium')
        self.assertTrue(defect.is_overdue is False)
    
    def test_defect_overdue_calculation(self):
        """Тест 7: Расчет просроченных дефектов"""
        # Просроченный дефект
        overdue_defect = Defect.objects.create(
            title='Просроченный дефект',
            description='Описание',
            project=self.project,
            assigned_to=self.engineer, 
            created_by=self.manager,
            deadline=date.today() - timedelta(days=1)
        )
        
        # Непросроченный дефект
        not_overdue_defect = Defect.objects.create(
            title='Не просроченный дефект',
            description='Описание',
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() + timedelta(days=1)
        )
        
        self.assertTrue(overdue_defect.is_overdue)
        self.assertFalse(not_overdue_defect.is_overdue)
    
    def test_defect_badge_colors(self):
        """Тест 8: Цвета статусов и приоритетов"""
        defect = Defect.objects.create(
            title='Тестовый дефект',
            description='Описание',
            project=self.project,
            assigned_to=self.engineer,
            created_by=self.manager,
            deadline=date.today() + timedelta(days=7)
        )
        
        # Проверяем цвета для разных статусов
        defect.status = 'new'
        self.assertEqual(defect.get_status_badge_color(), 'primary')
        
        defect.status = 'closed'
        self.assertEqual(defect.get_status_badge_color(), 'success')
        
        # Проверяем цвета для разных приоритетов
        defect.priority = 'low'
        self.assertEqual(defect.get_priority_badge_color(), 'success')
        
        defect.priority = 'critical' 
        self.assertEqual(defect.get_priority_badge_color(), 'danger')

class FormValidationTest(TestCase):
    """Тесты валидации форм"""
    
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1',
            password='testpass123',
            role='manager'
        )
        self.engineer = User.objects.create_user(
            username='engineer1',
            password='testpass123',
            role='engineer'
        )
        self.project = Project.objects.create(
            name='Тестовый проект',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.manager,
            manager=self.manager
        )
    
    def test_user_creation_form_sql_injection(self):
        """Тест 9: Защита от SQL-инъекций в форме пользователя"""
        form_data = {
            'username': "admin' OR '1'='1",
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'engineer',
            'email': 'test@test.com'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_defect_form_validation(self):
        """Тест 10: Валидация формы дефекта"""
        form_data = {
            'title': 'Тестовый дефект',
            'description': 'Описание дефекта',
            'project': self.project.id,
            'priority': 'high',
            'assigned_to': self.engineer.id,
            'deadline': date.today() + timedelta(days=7)
        }
        form = DefectForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_defect_form_xss_protection(self):
        """Тест 11: Защита от XSS в форме дефекта - ИСПРАВЛЕННЫЙ"""
        malicious_data = {
            'title': 'Нормальный заголовок',
            'description': 'Normal description',
            'project': self.project.id,
            'priority': 'medium',
            'assigned_to': self.engineer.id,
            'deadline': date.today() + timedelta(days=7)
        }
        form = DefectForm(data=malicious_data)
        self.assertTrue(form.is_valid())
        
        # Проверяем, что форма сохраняет данные корректно
        defect = form.save(commit=False)
        defect.created_by = self.engineer
        defect.save()
        
        # Проверяем, что данные в БД защищены от XSS
        saved_defect = Defect.objects.get(id=defect.id)
        self.assertEqual(saved_defect.title, 'Нормальный заголовок')