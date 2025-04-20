from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table
from django.core.exceptions import ValidationError
import re

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password1(self):
        password = self.cleaned_data.get("password1")


        if len(password) < 8:
            raise ValidationError("Пароль должен быть не менее 8 символов.")


        if not re.search(r'\d', password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")


        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву.")

        return password

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']


class GraphForm(forms.Form):
    table_choice = forms.ChoiceField(label='Выберите таблицу', choices=[])
    parameter_a = forms.FloatField(label='Параметр A')
    parameter_b = forms.FloatField(label='Параметр B')

    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)
        self.fields['table_choice'].choices = [(t.id, 'Таблица '+ str(t.id)) for t in Table.objects.all()]