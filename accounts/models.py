from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
import html

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('engineer', 'Инженер'),
        ('manager', 'Менеджер'),
        ('viewer', 'Руководитель/Заказчик'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='engineer',
        verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    # Решаем проблему с конфликтом имён
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='user',
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_engineer(self):
        return self.role == 'engineer'
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_viewer(self):
        return self.role == 'viewer'
    
    def clean(self):
        """Валидация данных пользователя"""
        if self.phone and not self.phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
            raise ValidationError('Некорректный формат телефона')

class Project(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название проекта')
    description = models.TextField(blank=True, verbose_name='Описание')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Создатель')
    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='managed_projects', verbose_name='Менеджер проекта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Защита от XSS при сохранении"""
        self.name = html.escape(self.name)
        self.description = html.escape(self.description)
        super().save(*args, **kwargs)
    
    def clean(self):
        """Валидация данных проекта"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Дата начала не может быть позже даты окончания')
    
    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

class Defect(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('checking', 'На проверке'),
        ('closed', 'Закрыта'),
        ('cancelled', 'Отменена'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Проект')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assigned_defects', verbose_name='Исполнитель')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_defects', verbose_name='Создатель')
    deadline = models.DateField(verbose_name='Срок устранения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def get_status_badge_color(self):
        status_colors = {
            'new': 'primary',
            'in_progress': 'warning', 
            'checking': 'info',
            'closed': 'success',
            'cancelled': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_priority_badge_color(self):
        priority_colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'critical': 'danger'
        }
        return priority_colors.get(self.priority, 'secondary')
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.deadline < date.today() and self.status not in ['closed', 'cancelled']
    
    def save(self, *args, **kwargs):
        """Защита от XSS при сохранении"""
        self.title = html.escape(self.title)
        self.description = html.escape(self.description)
        super().save(*args, **kwargs)
    
    def clean(self):
        """Валидация данных дефекта"""
        if self.deadline and self.project.start_date and self.deadline < self.project.start_date:
            raise ValidationError('Срок устранения не может быть раньше начала проекта')
        if self.deadline and self.project.end_date and self.deadline > self.project.end_date:
            raise ValidationError('Срок устранения не может быть позже окончания проекта')
    
    class Meta:
        verbose_name = 'Дефект'
        verbose_name_plural = 'Дефекты'

class DefectComment(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='comments', verbose_name='Дефект')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    def __str__(self):
        return f"Комментарий от {self.author} к {self.defect.title}"
    
    def save(self, *args, **kwargs):
        """Защита от XSS"""
        self.text = html.escape(self.text)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Комментарий дефекта'
        verbose_name_plural = 'Комментарии дефектов'

class DefectAttachment(models.Model):
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='attachments', verbose_name='Дефект')
    file = models.FileField(upload_to='defect_attachments/', verbose_name='Файл')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Загрузил')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    
    def __str__(self):
        return f"Вложение к {self.defect.title}"
    
    class Meta:
        verbose_name = 'Вложение дефекта'
        verbose_name_plural = 'Вложения дефектов'

class Task(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название задачи')
    description = models.TextField(verbose_name='Описание')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Исполнитель')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Проект')
    deadline = models.DateField(verbose_name='Срок выполнения')
    status = models.CharField(max_length=20, choices=Defect.STATUS_CHOICES, default='new', verbose_name='Статус')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_tasks', verbose_name='Создатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    def __str__(self):
        return self.title
    
    def get_status_badge_color(self):
        status_colors = {
            'new': 'primary',
            'in_progress': 'warning', 
            'checking': 'info',
            'closed': 'success',
            'cancelled': 'secondary'
        }
        return status_colors.get(self.status, 'secondary')
    
    def save(self, *args, **kwargs):
        """Защита от XSS при сохранении"""
        self.title = html.escape(self.title)
        self.description = html.escape(self.description)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

class Report(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название отчета')
    description = models.TextField(verbose_name='Описание')
    report_type = models.CharField(max_length=50, verbose_name='Тип отчета')
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Создатель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    file = models.FileField(upload_to='reports/', blank=True, null=True, verbose_name='Файл отчета')
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Защита от XSS при сохранении"""
        self.title = html.escape(self.title)
        self.description = html.escape(self.description)
        self.report_type = html.escape(self.report_type)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'