import math
import numpy as np

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm
from .models import Point, Table

from . import gauss, gauss_step, gradient, gradient_step, otzhig


def calculations(request):
    if request.method == 'POST':
        algorithm = request.POST.get('algorithm')

        if algorithm == 'gauss':
            context = {'a': gauss.gauss_a, 'b': gauss.gauss_b}
        elif algorithm == 'gauss_step':
            context = {'a': gauss_step.gauss_step_a, 'b': gauss_step.gauss_step_b}
        elif algorithm == 'gradient':
            context = {'a': gradient.gradient_a, 'b': gradient.gradient_b}
        elif algorithm == 'gradient_step':
            context = {'a': gradient_step.gradient_step_a, 'b': gradient_step.gradient_step_b}
        elif algorithm == 'otzhig':
            context = {'a': otzhig.otzhig_a, 'b': otzhig.otzhig_b}
        else:
            context = {}
    else:
        context = {}
    print(f"Контекст:{context}")

    return render(request, 'calculations.html', context)

def home_page(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home')

def graphs(request):
    return render(request, 'graphs.html')


@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)


@login_required
def delete_table(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'POST':
        table.delete()
        return redirect('databases')
    return redirect('databases')

def create_table(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        rows = data.strip().split('\n')
        temperature = float(rows[-1].split(';')[0])

        table = Table.objects.create(temperature=temperature)

        for row in rows[:-1]:
            x_value, y_value = map(float, row.split(';'))
            point = Point.objects.create(x_value=x_value, y_value=y_value)
            table.points.add(point)

        return HttpResponseRedirect('/databases/')

    return render(request, 'create_table.html')
