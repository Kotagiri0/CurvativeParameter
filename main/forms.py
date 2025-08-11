import json
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table, Profile, Post, CalculationResult, CustomAlgorithm
from .templatetags.string_filters import extract_comment


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
        widget=forms.TextInput(attrs={
            'placeholder': "Введите имя пользователя",
            'required': True
        })
    )
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={
            'placeholder': "Введите email",
            'required': True
        })
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Введите пароль",
            'required': True
        })
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Повторите пароль",
            'required': True
        })
    )

    error_messages = {
        'password_mismatch': "Пароли не совпадают.",
        'duplicate_username': "Это имя пользователя уже занято. Выберите другое.",
        'invalid_email': "Введите действительный адрес электронной почты.",
    }

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class GraphForm(forms.Form):
    table_choice = forms.ChoiceField(label='Выберите таблицу', choices=[])
    algorithm = forms.ChoiceField(label='Выберите алгоритм', choices=[
        ('gauss', 'Метод Гаусса'),
        ('gauss_step', 'Метод Гаусса с переменным шагом'),
        ('gradient', 'Метод градиентного спуска'),
        ('gradient_step', 'Метод градиентного спуска с переменным шагом'),
        ('otzhig', 'Метод симуляции отжига'),
    ])

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['table_choice'].choices = [(str(t.id), t.title) for t in Table.objects.all()]
        if user:
            custom_algorithms = CustomAlgorithm.objects.filter(user=user)
            custom_choices = [(f'custom_{algo.id}', f'Пользовательский: {algo.name}') for algo in custom_algorithms]
            self.fields['algorithm'].choices += custom_choices


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']


class PostForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Введите комментарий'}),
        label='Комментарий',
        required=False
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'calculation_result']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Введите заголовок'}),
            'content': forms.TextInput(),  # Скрываем полное поле content
            'image': forms.FileInput(),
            'calculation_result': forms.Select(),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Описание',
            'image': 'Изображение',
            'calculation_result': 'Результат расчёта',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['calculation_result'].queryset = CalculationResult.objects.filter(user=user)
        if self.instance and self.instance.content:
            self.fields['comment'].initial = extract_comment(self.instance.content)

    def save(self, commit=True):
        instance = super().save(commit=False)
        new_comment = self.cleaned_data['comment']
        calc_result = self.cleaned_data['calculation_result']
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
                *table_lines
            ]
            if new_comment.strip():
                content_lines.append(new_comment)
            instance.content = "\n".join(content_lines)
        else:
            instance.content = new_comment if new_comment.strip() else ""

        if commit:
            instance.save()
        return instance


class CustomAlgorithmForm(forms.ModelForm):
    class Meta:
        model = CustomAlgorithm
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Введите название алгоритма'}),
            'code': forms.Textarea(attrs={'placeholder': 'Вставьте код Python алгоритма', 'rows': 10}),
            'description': forms.Textarea(attrs={'placeholder': 'Опишите ваш алгоритм', 'rows': 4}),
        }
        labels = {
            'name': 'Название',
            'code': 'Код алгоритма',
            'description': 'Описание',
        }