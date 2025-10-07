from django import forms

class DefectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        from .models import Defect, CustomUser
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор исполнителей только инженерами
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

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

class DefectUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        from .models import CustomUser
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор исполнителей только инженерами
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(role='engineer')

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