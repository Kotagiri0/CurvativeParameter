import json

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table, Profile, Post, CalculationResult
from .templatetags.string_filters import extract_comment


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=("Имя пользователя"),
        widget=forms.TextInput(attrs={
            'placeholder': ("Введите имя пользователя"),
            'required': True,
            'id': 'username'
        })
    )
    password = forms.CharField(
        label=("Пароль"),
        widget=forms.PasswordInput(attrs={
            'placeholder': ("Введите пароль"),
            'required': True,
            'id': 'password'
        })
    )

    error_messages = {
        'invalid_login': ("Неверное имя пользователя или пароль. Оба поля чувствительны к регистру."),
        'inactive': ("Этот аккаунт неактивен. Обратитесь к администратору."),
    }

    class Meta:
        model = User
        fields = ['username', 'password']

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label=("Имя пользователя"),
        widget=forms.TextInput(attrs={
            'placeholder': ("Введите имя пользователя"),
            'required': True
        })
    )
    email = forms.EmailField(
        label=("Электронная почта"),
        widget=forms.EmailInput(attrs={
            'placeholder': ("Введите email"),
            'required': True
        })
    )
    password1 = forms.CharField(
        label=("Пароль"),
        widget=forms.PasswordInput(attrs={
            'placeholder': ("Введите пароль"),
            'required': True
        })
    )
    password2 = forms.CharField(
        label=("Подтверждение пароля"),
        widget=forms.PasswordInput(attrs={
            'placeholder': ("Повторите пароль"),
            'required': True
        })
    )

    error_messages = {
        'password_mismatch': ("Пароли не совпадают."),
        'duplicate_username': ("Это имя пользователя уже занято. Выберите другое."),
        'invalid_email': ("Введите действительный адрес электронной почты."),
    }

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


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

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']


from django import forms
from .models import Post, CalculationResult, Comment


class PostForm(forms.ModelForm):
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
            'average_error'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Введите текст поста...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'calculation_result': forms.Select(attrs={
                'class': 'form-control'
            }),
            'algorithm': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Метод Гаусса (опционально)'
            }),
            'a12': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Значение A₁₂ (опционально)'
            }),
            'a21': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Значение A₂₁ (опционально)'
            }),
            'iterations': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Количество итераций (опционально)'
            }),
            'exec_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Время выполнения (опционально)'
            }),
            'average_error': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Средняя погрешность % (опционально)'
            }),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Описание',
            'image': 'Изображение (опционально)',
            'calculation_result': 'Привязать к расчёту (опционально)',
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

        # Показываем пользователю только его расчёты
        if user:
            self.fields['calculation_result'].queryset = CalculationResult.objects.filter(user=user)

        # Делаем calculation_result необязательным
        self.fields['calculation_result'].required = False

        # Все технические поля тоже необязательны
        self.fields['algorithm'].required = False
        self.fields['a12'].required = False
        self.fields['a21'].required = False
        self.fields['iterations'].required = False
        self.fields['exec_time'].required = False
        self.fields['average_error'].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите комментарий...'
            })
        }
        labels = {
            'content': 'Комментарий'
        }