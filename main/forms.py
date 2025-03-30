from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Table

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']


class GraphForm(forms.Form):
    table_choice = forms.ChoiceField(label='Выберите таблицу', choices=[])
    parameter_a = forms.FloatField(label='Параметр A')
    parameter_b = forms.FloatField(label='Параметр B')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table_choice'].choices = [(t.id, 'Таблица '+ str(t.id)) for t in Table.objects.all()]
