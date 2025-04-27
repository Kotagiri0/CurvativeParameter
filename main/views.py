import base64
import math
import traceback

import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm, GraphForm, UserUpdateForm, ProfileUpdateForm
from .models import Point, Table, CalculationResult, Profile
from django.http import JsonResponse
from . import gauss, gauss_step, gradient, gradient_step, otzhig
from .forms import LoginForm
param_a, param_b = 0, 0
from django.shortcuts import render, redirect
from django.contrib import messages
from .gmail import validate_gmail

@login_required
def graph_view(request):
    # Get parameters from session
    result_id = request.session.get('result_id')
    table_id = request.session.get('table_id')
    param_a = request.session.get('param_a')
    param_b = request.session.get('param_b')

    # Set initial form data
    initial_data = {}
    if result_id:
        try:
            result = CalculationResult.objects.get(id=result_id)
            initial_data = {
                'table_choice': str(table_id) if table_id is not None else None,
                'parameter_a': round(result.param_a, 3),
                'parameter_b': round(result.param_b, 3),
            }
        except CalculationResult.DoesNotExist:
            if table_id:
                initial_data['table_choice'] = str(table_id)
            if param_a is not None:
                initial_data['parameter_a'] = round(param_a, 3)
            if param_b is not None:
                initial_data['parameter_b'] = round(param_b, 3)

    form = GraphForm(request.POST or None, initial=initial_data)
    context = {'form': form}

    if request.method == 'POST' and form.is_valid():
        # Get form data
        table_id = int(form.cleaned_data['table_choice'])
        table = Table.objects.get(id=table_id)
        parameter_a = float(form.cleaned_data['parameter_a'])
        parameter_b = float(form.cleaned_data['parameter_b'])



        # Create plot data
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

        # Build the graph
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(new_x, new_y, color='red', marker='o', markersize=1)
        ax.scatter(xx, yy, color='b')
        plt.title(table.title[:-1])
        ax.set_xlabel(r'$x_2$')
        ax.set_ylabel(r'$G^{E}$')
        ax.grid(True)

        # Save graph to memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close(fig)

        # Encode image to base64
        graphic = base64.b64encode(image_png).decode('utf-8')

        context.update({
            'graphic': graphic,
            'a': round(parameter_a, 3),
            'b': round(parameter_b, 3)
        })

    # Add parameters to context for display
    if param_a is not None and param_b is not None:
        context.update({'a': round(param_a, 3), 'b': round(param_b, 3)})

    print(f"Контекст: {context}")
    return render(request, 'graphs.html', context)

@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)

@login_required
def delete_result(request, result_id):
    result = get_object_or_404(CalculationResult, id=result_id)

    if request.user == result.user:
        result.delete()

    return redirect('profile')


from django.contrib.auth.decorators import login_required
from main.models import Profile, CalculationResult
from main.forms import UserUpdateForm, ProfileUpdateForm

@login_required
def profile(request):
    context = {}
    Profile.objects.get_or_create(user=request.user)
    user_results = CalculationResult.objects.filter(user=request.user).order_by('-created_at')

    # Проверка, привязан ли соц аккаунт
    has_social_account = request.user.social_auth.exists()
    context['has_social_account'] = has_social_account

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context.update({
        'user': request.user,
        'user_form': user_form,
        'profile_form': profile_form,
        'user_results': user_results,
    })

    return render(request, 'profile.html', context)


@login_required
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        avatar = request.FILES.get('avatar')  # Получаем файл аватара из формы

        user = request.user

        # Проверка на уникальность имени пользователя
        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, 'Имя пользователя уже занято.')
            return redirect('profile')

        # Проверка на уникальность email
        if request.method == 'POST':
            email = request.POST.get('email')

            # Вызов функции валидации Gmail
            validation_result = validate_gmail(request, user, email)
            if validation_result:
                return validation_result

            # Если валидация прошла, обновляем email
            user.email = email
            user.save()
            messages.success(request, 'Email успешно обновлен.')
            return redirect('profile')
        try:
            # Обновляем данные пользователя
            user.username = username
            user.email = email
            user.save()

            # Обновляем или создаем профиль с аватаром
            profile, created = Profile.objects.get_or_create(user=user)
            if avatar:  # Если аватар был загружен
                profile.avatar = avatar
                profile.save()

            messages.success(request, 'Профиль успешно обновлен.')
        except ValueError as e:
            messages.error(request, f'Ошибка при обновлении профиля: {str(e)}')

        return redirect('profile')

    # Если метод не POST, перенаправляем на страницу профиля
    return redirect('profile')

@login_required
def calculations(request):
    tables = Table.objects.all()
    context = {"tables": tables}

    if request.method == 'POST':
        try:
            algorithm = request.POST.get('algorithm')
            table_id = int(request.POST.get('tabledata')) - 1
            response_data = {
                'algorithm': algorithm,
                'iterations': 'N/A',
                'exec_time': 'N/A',
                'table_data': []
            }

            # Логика для каждого алгоритма
            if algorithm == 'gauss':
                gauss_a, gauss_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gauss.gauss(tables, table_id)
                table_data = [
                    {'x2': x2, 'gmod': gmod, 'gexp': gexp, 'sigma': op, 'delta': ap}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=tables[table_id].title,
                    algorithm='Метод Гаусса',
                    param_a=gauss_a,
                    param_b=gauss_b,
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=table_data
                )

                response_data.update({
                    'a': round(gauss_a, 3),
                    'b': round(gauss_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

            elif algorithm == 'gauss_step':
                gauss_step_a, gauss_step_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gauss_step.gauss_step(tables, table_id)
                table_data = [
                    {'x2': x2, 'gmod': gmod, 'gexp': gexp, 'sigma': op, 'delta': ap}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=tables[table_id].title,
                    algorithm='Метод Гаусса с переменным шагом',
                    param_a=gauss_step_a,
                    param_b=gauss_step_b,
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=table_data
                )

                response_data.update({
                    'c': round(gauss_step_a, 3),
                    'd': round(gauss_step_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

            elif algorithm == 'gradient':
                gradient_a, gradient_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gradient.gradient(tables, table_id)
                table_data = [
                    {'x2': x2, 'gmod': gmod, 'gexp': gexp, 'sigma': op, 'delta': ap}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=tables[table_id].title,
                    algorithm='Метод градиентного спуска',
                    param_a=gradient_a,
                    param_b=gradient_b,
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=table_data
                )

                response_data.update({
                    'e': round(gradient_a, 3),
                    'f': round(gradient_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

            elif algorithm == 'gradient_step':
                gradient_step_a, gradient_step_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gradient_step.gradient_step(tables, table_id)
                table_data = [
                    {'x2': x2, 'gmod': gmod, 'gexp': gexp, 'sigma': op, 'delta': ap}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=tables[table_id].title,
                    algorithm='Метод градиентного спуска с переменным шагом',
                    param_a=gradient_step_a,
                    param_b=gradient_step_b,
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=table_data
                )

                response_data.update({
                    'g': round(gradient_step_a, 3),
                    'h': round(gradient_step_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

            elif algorithm == 'otzhig':
                otzhig_a, otzhig_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = otzhig.otzhig(tables, table_id)
                table_data = [
                    {'x2': x2, 'gmod': gmod, 'gexp': gexp, 'sigma': op, 'delta': ap}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=tables[table_id].title,
                    algorithm='Метод симуляции отжига',
                    param_a=otzhig_a,
                    param_b=otzhig_b,
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=table_data
                )

                response_data.update({
                    'i': round(otzhig_a, 3),
                    'j': round(otzhig_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

            # Сохранение в сессии (если нужно)
            request.session['param_a'] = response_data.get('a') or response_data.get('c') or response_data.get('e') or response_data.get('g') or response_data.get('i')
            request.session['param_b'] = response_data.get('b') or response_data.get('d') or response_data.get('f') or response_data.get('h') or response_data.get('j')
            request.session['result_id'] = result.id
            request.session['table_choice'] = table_id
            request.session.modified = True

            return JsonResponse(response_data)
        except Exception as e:
            print(traceback.format_exc())  # Логирование ошибки
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'calculations.html', context)

@login_required
def home_page(request):
    return render(request, 'index.html')
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import RegisterForm
from .gmail import validate_gmail

from django.contrib.auth import login
from django.contrib.auth.backends import ModelBackend  # Добавляем
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import RegisterForm  # Предполагаю, что RegisterForm импортируется

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')

            # Проверка на уникальность email
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Этот email уже используется.')
                return render(request, 'register.html', {'form': form})

            # Вызов функции валидации Gmail
            user = form.save(commit=False)  # Создаем пользователя, но не сохраняем в БД
            validation_result = validate_gmail(request, user, email)
            if validation_result:
                return validation_result

            # Если валидация прошла, сохраняем пользователя
            user.email = email
            user.save()
            # Указываем бэкенд явно
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация успешно завершена.')
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
