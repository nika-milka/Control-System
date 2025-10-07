from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import html

class SafeFormMixin:
    """Миксин для защиты от XSS и SQL-инъекций"""
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Экранирование HTML во всех текстовых полях
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                # Защита от XSS
                cleaned_data[field_name] = html.escape(value)
        
        return cleaned_data

# Базовые формы для пользователей
class CustomUserCreationForm(SafeFormMixin, UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите телефон'
        })
    )
    role = forms.ChoiceField(
        choices=[],  # Будет установлено в __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Выберите роль пользователя"
    )

    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = CustomUser.ROLE_CHOICES
        
        # Упрощаем подсказки для полей
        self.fields['username'].widget.attrs.update({'placeholder': 'Придумайте логин'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Придумайте пароль'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Повторите пароль'})
        
        for field_name, field in self.fields.items():
            if field_name not in ['role']:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username']
        # Защита от SQL-инъекций
        if any(char in username for char in ['"', "'", ';', '--']):
            raise ValidationError('Недопустимые символы в имени пользователя')
        return username
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Валидация телефона
        if phone and not phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
            raise ValidationError('Некорректный формат телефона')
        return phone

    class Meta:
        from .models import CustomUser
        model = CustomUser
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')

class CustomAuthenticationForm(SafeFormMixin, AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Введите пароль'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        # Защита от SQL-инъекций
        if any(char in username for char in ['"', "'", ';', '--']):
            raise ValidationError('Недопустимые символы в имени пользователя')
        return username

class DefectForm(forms.ModelForm):
    class Meta:
        from .models import Defect
        model = Defect
        fields = ['title', 'description', 'project', 'priority', 'assigned_to', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок дефекта'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Подробное описание дефекта'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор исполнителей только инженерами
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

class DefectUpdateForm(forms.ModelForm):
    class Meta:
        from .models import Defect
        model = Defect
        fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор исполнителей только инженерами
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

class DefectCommentForm(forms.ModelForm):
    class Meta:
        from .models import DefectComment
        model = DefectComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите ваш комментарий...'}),
        }

class DefectAttachmentForm(forms.ModelForm):
    class Meta:
        from .models import DefectAttachment
        model = DefectAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }