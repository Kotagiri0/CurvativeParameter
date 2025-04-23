from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table, Profile


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
