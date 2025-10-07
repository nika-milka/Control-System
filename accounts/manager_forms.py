from django import forms

class TaskForm(forms.ModelForm):
    class Meta:
        from .models import Task, CustomUser, Project
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название задачи'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание задачи'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        # Только инженеры могут быть исполнителями
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

class DefectAssignmentForm(forms.ModelForm):
    class Meta:
        from .models import Defect
        model = Defect
        fields = ['assigned_to', 'deadline', 'priority']
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

class ProjectForm(forms.ModelForm):
    class Meta:
        from .models import Project
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название проекта'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Описание проекта'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        # Только менеджеры могут быть управляющими проектов
        self.fields['manager'].queryset = CustomUser.objects.filter(role='manager')