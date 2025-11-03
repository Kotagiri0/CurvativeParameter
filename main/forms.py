import json
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table, Profile, Post, CalculationResult, Comment
from .templatetags.string_filters import extract_comment


# ======== Аутентификация и регистрация ========

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={
            'placeholder': "Введите имя пользователя",
            'required': True,
            'id': 'username'
        })
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Введите пароль",
            'required': True,
            'id': 'password'
        })
    )

    error_messages = {
        'invalid_login': "Неверное имя пользователя или пароль. Оба поля чувствительны к регистру.",
        'inactive': "Этот аккаунт неактивен. Обратитесь к администратору.",
    }

    class Meta:
        model = User
        fields = ['username', 'password']


class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Имя пользователя",
        widget=forms.TextInput(attrs={'placeholder': "Введите имя пользователя", 'required': True})
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={'placeholder': "Введите email", 'required': True})
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'placeholder': "Введите пароль", 'required': True})
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={'placeholder': "Повторите пароль", 'required': True})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Эта электронная почта уже используется.")
        return email


# ======== Графики и профили ========

class GraphForm(forms.Form):
    table_choice = forms.ChoiceField(label='Выберите таблицу', choices=[])
    parameter_a = forms.FloatField(label='Параметр A')
    parameter_b = forms.FloatField(label='Параметр B')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table_choice'].choices = [(str(t.id), t.title) for t in Table.objects.all()]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("Эта электронная почта уже используется.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']


# ======== Посты ========

class PostForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Введите комментарий...'}),
        label='Комментарий',
        required=False
    )

    class Meta:
        model = Post
        fields = [
            'title',
            'content',
            'image',
            'calculation_result',
            'algorithm',
            'a12',
            'a21',
            'iterations',
            'exec_time',
            'average_error',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Введите текст поста...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'calculation_result': forms.Select(attrs={'class': 'form-control'}),
            'algorithm': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Алгоритм (опционально)'}),
            'a12': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A₁₂ (опционально)'}),
            'a21': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A₂₁ (опционально)'}),
            'iterations': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Итерации (опционально)'}),
            'exec_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Время выполнения (сек)'}),
            'average_error': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Средняя погрешность %'}),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Описание',
            'image': 'Изображение (опционально)',
            'calculation_result': 'Результат расчёта (опционально)',
            'algorithm': 'Алгоритм',
            'a12': 'A₁₂',
            'a21': 'A₂₁',
            'iterations': 'Итерации',
            'exec_time': 'Время выполнения',
            'average_error': 'Средняя погрешность (%)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['calculation_result'].queryset = CalculationResult.objects.filter(user=user)

        for field in ['calculation_result', 'algorithm', 'a12', 'a21', 'iterations', 'exec_time', 'average_error']:
            self.fields[field].required = False

        # Автоматическое заполнение комментария, если контент уже есть
        if self.instance and self.instance.content:
            self.fields['comment'].initial = extract_comment(self.instance.content)

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_comment = self.cleaned_data.get('comment', '')
        calc_result = self.cleaned_data.get('calculation_result')

        if calc_result:
            table_data = json.loads(calc_result.table_data) if calc_result.table_data else []
            table_lines = [",".join(map(str, row.values())) for row in table_data]
            content_lines = [
                f"Название: {calc_result.title}",
                f"Параметр A: {calc_result.param_a}",
                f"Параметр B: {calc_result.param_b}",
                f"Итерации: {calc_result.iterations}",
                f"Время выполнения: {calc_result.exec_time} сек",
                f"Алгоритм: {calc_result.algorithm}",
                f"Средняя погрешность: {calc_result.average_op}%",
                "Данные таблицы:",
                *table_lines,
            ]
            if new_comment.strip():
                content_lines.append(new_comment)
            instance.content = "\n".join(content_lines)
        else:
            instance.content = new_comment.strip() if new_comment.strip() else ""

        if commit:
            instance.save()
        return instance


# ======== Комментарии ========

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите комментарий...'})
        }
        labels = {'content': 'Комментарий'}
