import base64
import math
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm, GraphForm
from .models import Point, Table
from django.http import JsonResponse
from . import gauss, gauss_step, gradient, gradient_step, otzhig
from .forms import LoginForm
param_a, param_b = 0, 0

@login_required
def graph_view(request):
    form = GraphForm()
    if request.method == 'POST':
        form = GraphForm(request.POST)
        if form.is_valid():
            # Получаем выбранную таблицу и параметры
            table_id = int(form.cleaned_data['table_choice'])
            table = Table.objects.get(id=table_id)
            parameter_a = float(form.cleaned_data['parameter_a'])
            parameter_b = float(form.cleaned_data['parameter_b'])

            # Создаем список точек для построения графика
            new_y = []
            new_x = np.linspace(0, 1, 10000)

            xx = []
            yy = []
            for point in table.points.all():
                xx.append(point.x_value)
                yy.append(point.y_value)


            for point in new_x:
                x1 = 1 - point
                rt = table.temperature * 8.314462618
                y_value = rt * x1 * point * (x1 * parameter_a + point * parameter_b)
                new_y.append(y_value)

            # Строим график
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(new_x, new_y, color='red', marker='o', markersize=1)
            ax.scatter(xx, yy, color='b')
            ax.set_xlabel('x2')
            ax.set_ylabel('Ge')
            ax.grid(True)

            # Сохраняем график в память
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()

            # Кодируем изображение в base64 для отображения в HTML
            graphic = base64.b64encode(image_png).decode('utf-8')

            context = {
                'form': form,
                'graphic': graphic,
                'a': param_a,
                'b': param_b
            }
            return render(request, 'graphs.html', context)

    context = {'form': form, 'a': param_a, 'b': param_b}
    print("Контекст", context)
    return render(request, 'graphs.html', context)

@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)

@login_required
def profile(request):
    if request.method == 'POST':
        context = {
            'username': request.user.username,
            'password': request.user.password
        }
        return JsonResponse(context)
    else:
        context = {
            'username': request.user.username,
            'password': request.user.password
        }
        return JsonResponse(context)

@login_required
def calculations(request):
    tables = Table.objects.all()
    if request.method == 'POST':
        algorithm = request.POST.get('algorithm')
        table_id = int(request.POST.get('tabledata')) - 1

        if algorithm == 'gauss':
            gauss_a, gauss_b = gauss.gauss(tables, table_id)
            param_a, param_b = gauss_a, gauss_b
            context = {'a': round(gauss_a, 3), 'b': round(gauss_b, 3)}

        elif algorithm == 'gauss_step':
            gauss_step_a, gauss_step_b = gauss_step.gauss_step(tables, table_id)
            param_a, param_b = gauss_step_a, gauss_step_b
            context = {'c': round(gauss_step_a, 3), 'd': round(gauss_step_b, 3)}

        elif algorithm == 'gradient':
            gradient_a, gradient_b = gradient.gradient(tables, table_id)
            param_a, param_b = gradient_a, gradient_b
            context = {'e': round(gradient_a, 3), 'f': round(gradient_b, 3)}

        elif algorithm == 'gradient_step':
            gradient_step_a, gradient_step_b = gradient_step.gradient_step(tables, table_id)
            param_a, param_b = gradient_step_a, gradient_step_b
            context = {'g': round(gradient_step_a, 3), 'h': round(gradient_step_b, 3)}

        elif algorithm == 'otzhig':
            otzhig_a, otzhig_b = otzhig.otzhig(tables, table_id)
            param_a, param_b = otzhig_a, otzhig_b
            context = {'i': round(otzhig_a, 3), 'j': round(otzhig_b, 3)}
        else:
            context = {}
    else:
        context = {}
    context["tables"] = tables
    print(f"Контекст:{context}")

    return render(request, 'calculations.html', context)
@login_required
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
@login_required
def logout_user(request):
    logout(request)
    return redirect('home')



@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)


@login_required
def delete_table(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if request.method == 'GET':
        table.delete()
        return redirect('databases')
    return redirect('databases')
@login_required
def create_table(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        rows = data.strip().split('\n')
        temperature = float(rows[-1])
        title = rows[0]
        solution = rows[1]
        table = Table.objects.create(temperature=temperature, title=title, solution=solution)
        for row in rows[2:-1]:
            x_value, y_value = map(float, row.split(';'))
            point = Point.objects.create(x_value=x_value, y_value=y_value)
            table.points.add(point)
        return HttpResponseRedirect('/databases/')

    return render(request, 'create_table.html')
