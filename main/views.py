import base64
import json
import math
import traceback
from datetime import time

import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models.expressions import result
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, LoginForm, GraphForm, UserUpdateForm, ProfileUpdateForm, PostForm
from .models import Point, Table, CalculationResult, Profile, Post
from django.http import JsonResponse
from . import gauss, gauss_step, gradient, gradient_step, otzhig
from .forms import LoginForm
param_a, param_b = 0, 0

@login_required
def forum_list(request):
    query = request.GET.get('q', '')
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(calculation_result__title__icontains=query) |
            Q(calculation_result__algorithm__icontains=query)
        ).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')
    return render(request, 'forum_list.html', {'posts': posts, 'query': query})

@login_required
def forum_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    # Получаем расчетные данные, если они существуют
    try:
        calculation_result = post.calculation_result  # Исправлено на calculation
    except AttributeError:
        print(f"Ошибка: поле calculation не найдено в модели Post. Доступные поля: {dir(post)}")
        calculation_result = None
    except CalculationResult.DoesNotExist:
        calculation_result = None

    # Разделяем содержимое поста по строкам и парсим данные
    lines = post.content.split("\n")
    data_lines = []

    for line in lines:
        if line.strip():  # Игнорируем пустые строки
            try:
                parts = line.split(',')
                if len(parts) == 5:  # Если строка имеет 5 значений
                    x2 = parts[0].strip()
                    gexp = parts[1].strip()
                    gmod = parts[2].strip()
                    sigma = parts[3].strip().replace('%', '')
                    delta = parts[4].strip()

                    try:
                        x2 = str(float(x2))[0:5] if x2 != 'N/A' else '0.000'
                        gexp = float(gexp) if gexp != 'N/A' else '0.0'
                        gmod = float(gmod) if gmod != 'N/A' else '0.0'
                        sigma = float(sigma) if sigma != 'N/A' else '0.0'
                        delta = float(delta) if delta != 'N/A' else '0.0'
                    except ValueError as e:
                        print(f"Ошибка преобразования строки в числа: {line}, ошибка: {e}")
                        continue

                    data_lines.append({
                        'x2': x2,
                        'gexp': gexp,
                        'gmod': gmod,
                        'sigma': sigma,
                        'delta': delta,
                    })
            except Exception as e:
                print(f"Ошибка при обработке строки: {line}, ошибка: {e}")

    # Получаем информацию о расчете, если она существует
    if calculation_result:
        result_info = {
            'param_a': calculation_result.param_a,
            'param_b': calculation_result.param_b,
            'iterations': calculation_result.iterations,
            'exec_time': calculation_result.exec_time,
            'algorithm': calculation_result.algorithm,
            'average_error': calculation_result.average_op,
        }
    else:
        # Если calculation_result недоступен, парсим данные из post.content
        result_info = {}
        for line in lines:
            if line.startswith("Параметр A:"):
                result_info['param_a'] = float(line.split(":")[1].strip())
            elif line.startswith("Параметр B:"):
                result_info['param_b'] = float(line.split(":")[1].strip())
            elif line.startswith("Итерации:"):
                result_info['iterations'] = int(line.split(":")[1].strip()) if line.split(":")[1].strip() != 'N/A' else 'N/A'
            elif line.startswith("Время выполнения:"):
                time_str = line.split(":")[1].strip()
                result_info['exec_time'] = float(time_str.replace(" сек", "")) if time_str != 'N/A' else None
            elif line.startswith("Алгоритм:"):
                result_info['algorithm'] = line.split(":")[1].strip()
            elif line.startswith("Средняя погрешность:"):
                error_str = line.split(":")[1].strip()
                result_info['average_error'] = float(error_str.replace("%", "")) if error_str != 'N/A' else None

    # Передаем данные в шаблон
    return render(request, 'forum_detail.html', {
        'post': post,
        'data_lines': data_lines,
        'result_info': result_info
    })

# Создание нового поста
@login_required
def forum_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Пост успешно создан!')
            return redirect('forum_list')
    else:
        form = PostForm()
    return render(request, 'forum_create.html', {'form': form})

@login_required
def forum_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user and request.method == "POST":
        post.delete()
    return redirect('forum_list')


@login_required
def forum_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('forum_list')

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('forum_detail', post_id=post.pk)
    else:
        form = PostForm(instance=post, user=request.user)

    return render(request, 'forum_edit.html', {'form': form, 'post': post})

@login_required
def share_calculation(request, result_id):
    result = get_object_or_404(CalculationResult, id=result_id)
    print(f"CalculationResult #{result.id}:")
    print(f"algorithm: {result.algorithm}")
    print(f"average_op: {result.average_op}")
    print(f"table_data: {result.table_data}")
    print(f"get_table_data(): {result.get_table_data()}")

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.calculation_result = result

            # Формируем содержимое поста с данными расчета
            table_data = result.get_table_data()
            table_data_str = "Нет данных таблицы."

            if table_data:
                try:
                    if isinstance(table_data, list):
                        table_data_str = "\n".join([
                            f"{row.get('x2', 'N/A')},{row.get('gexp', 'N/A')},{row.get('gmod', 'N/A')},{row.get('sigma', 'N/A')},{row.get('delta', 'N/A')}"
                            for row in table_data if isinstance(row, dict)
                        ])
                    else:
                        table_data_str = "Ошибка в данных таблицы"
                except Exception as e:
                    table_data_str = f"Ошибка при обработке данных таблицы: {str(e)}"

            # Формируем пост content
            content_lines = [
                f"Результат расчета #{result.id}:",
                f"Название: {result.title}",
                f"Параметр A: {result.param_a:.3f}",
                f"Параметр B: {result.param_b:.3f}",
                f"Итерации: {result.iterations if result.iterations is not None else 'N/A'}",
            ]

            if result.exec_time is not None:
                content_lines.append(f"Время выполнения: {result.exec_time:.2f} сек")
            else:
                content_lines.append("Время выполнения: N/A")

            content_lines.append(f"Алгоритм: {result.algorithm if result.algorithm else 'Не указан'}")

            if result.average_op is not None:
                content_lines.append(f"Средняя погрешность: {result.average_op:.1f}%")
            else:
                content_lines.append("Средняя погрешность: N/A")

            content_lines.append("Данные таблицы:")
            content_lines.append(table_data_str)
            content_lines.append("")  # Пустая строка перед пользовательским комментарием

            user_content = form.cleaned_data['content'].strip()
            if user_content:  # Добавляем комментарий только если он не пустой
                content_lines.append(user_content)

            post.content = "\n".join(content_lines)

            print(f"Post content:\n{post.content}")
            post.save()
            messages.success(request, 'Результат расчета успешно опубликован на форуме!')
            return redirect('forum_list')
    else:
        table_data = result.get_table_data()
        table_data_str = "Нет данных таблицы."
        if table_data:
            try:
                if isinstance(table_data, list):
                    table_data_str = "\n".join([
                        f"{row.get('x2', 'N/A')},{row.get('gexp', 'N/A')},{row.get('gmod', 'N/A')},{row.get('sigma', 'N/A')},{row.get('delta', 'N/A')}"
                        for row in table_data if isinstance(row, dict)
                    ])
                else:
                    table_data_str = "Ошибка в данных таблицы"
            except Exception as e:
                table_data_str = f"Ошибка при обработке данных таблицы: {str(e)}"

        initial_data = {
            'title': f'Результат расчета #{result.id}',
            'content': ""  # Пустое начальное значение
        }
        form = PostForm(initial=initial_data)

    return render(request, 'forum_create.html', {'form': form, 'result': result})

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
            if table_id is not None:
                initial_data['table_choice'] = str(table_id)
            if param_a is not None:
                initial_data['parameter_a'] = round(param_a, 3)
            if param_b is not None:
                initial_data['parameter_b'] = round(param_b, 3)
    else:
        if table_id is not None:
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

        # Save parameters and table choice to session
        request.session['table_id'] = table_id
        request.session['param_a'] = parameter_a
        request.session['param_b'] = parameter_b
        request.session.modified = True

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

        # Save graph to memory for display
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        graphic = base64.b64encode(image_png).decode('utf-8')

        # Формируем table_data (для отображения, но не для сохранения)
        table_data = []
        for x, y_exp in zip(xx, yy):
            x1 = 1 - x
            rt = table.temperature * 8.314462618
            y_mod = rt * x1 * x * (x1 * parameter_a + x * parameter_b)
            delta = abs(y_exp - y_mod)
            sigma = (delta / y_exp * 100) if y_exp != 0 else 0
            table_data.append({
                "x2": x,
                "gmod": y_mod,
                "gexp": y_exp,
                "sigma": sigma,
                "delta": delta
            })

        # Update session with the new result_id
        request.session['result_id'] = result.id

        buffer.close()
        plt.close(fig)

        context.update({
            'graphic': graphic,
            'a': round(parameter_a, 3),
            'b': round(parameter_b, 3),
            'result_id': result.id,
            'graphic_result': result,  # Передаем объект результата для отображения в graphs.html
        })

    # Add parameters to context for display
    if param_a is not None and param_b is not None:
        context.update({'a': round(param_a, 3), 'b': round(param_b, 3)})

    print(f"Контекст: {context}")
    print(f"Initial data: {initial_data}")
    print(f"Table ID from session: {table_id}")
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


@login_required
def profile(request):
    context = {}
    Profile.objects.get_or_create(user=request.user)
    user_results = CalculationResult.objects.filter(user=request.user).order_by('-created_at')
    if request.method == 'POST':
        context['user_results'] = user_results
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context.update({
        'user': request.user,
        'user_form': user_form,
        'profile_form': profile_form,
        'user_results': user_results
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
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            messages.error(request, 'Электронная почта уже используется.')
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
            table = tables[table_id]  # Получаем объект Table
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
                    {'x2': float(x2), 'gmod': float(gmod), 'gexp': float(gexp), 'sigma': float(op), 'delta': float(ap)}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=table.title,
                    algorithm='Метод Гаусса',
                    param_a=gauss_a,
                    param_b=gauss_b,
                    table=table,  # Передаем объект Table
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=json.dumps(table_data)  # Сериализуем в JSON
                )

                response_data.update({
                    'a': round(gauss_a, 3),
                    'b': round(gauss_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

                context.update({
                    'result': result,  # Передаем результат в шаблон
                    'table_data': table_data  # Передаем данные таблицы в шаблон
                })

            elif algorithm == 'gauss_step':
                gauss_step_a, gauss_step_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gauss_step.gauss_step(tables, table_id)
                table_data = [
                    {'x2': float(x2), 'gmod': float(gmod), 'gexp': float(gexp), 'sigma': float(op), 'delta': float(ap)}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=table.title,
                    algorithm='Метод Гаусса с переменным шагом',
                    param_a=gauss_step_a,
                    param_b=gauss_step_b,
                    table=table,  # Передаем объект Table
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=json.dumps(table_data)  # Сериализуем в JSON
                )

                response_data.update({
                    'c': round(gauss_step_a, 3),
                    'd': round(gauss_step_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

                context.update({
                    'result': result,  # Передаем результат в шаблон
                    'table_data': table_data  # Передаем данные таблицы в шаблон
                })

            elif algorithm == 'gradient':
                gradient_a, gradient_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gradient.gradient(tables, table_id)
                table_data = [
                    {'x2': float(x2), 'gmod': float(gmod), 'gexp': float(gexp), 'sigma': float(op), 'delta': float(ap)}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=table.title,
                    algorithm='Метод градиентного спуска',
                    param_a=gradient_a,
                    param_b=gradient_b,
                    table=table,  # Передаем объект Table
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=json.dumps(table_data)  # Сериализуем в JSON
                )

                response_data.update({
                    'e': round(gradient_a, 3),
                    'f': round(gradient_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

                context.update({
                    'result': result,  # Передаем результат в шаблон
                    'table_data': table_data  # Передаем данные таблицы в шаблон
                })

            elif algorithm == 'gradient_step':
                gradient_step_a, gradient_step_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = gradient_step.gradient_step(tables, table_id)
                table_data = [
                    {'x2': float(x2), 'gmod': float(gmod), 'gexp': float(gexp), 'sigma': float(op), 'delta': float(ap)}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=table.title,
                    algorithm='Метод градиентного спуска с переменным шагом',
                    param_a=gradient_step_a,
                    param_b=gradient_step_b,
                    table=table,  # Передаем объект Table
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=json.dumps(table_data)  # Сериализуем в JSON
                )

                response_data.update({
                    'g': round(gradient_step_a, 3),
                    'h': round(gradient_step_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

                context.update({
                    'result': result,  # Передаем результат в шаблон
                    'table_data': table_data  # Передаем данные таблицы в шаблон
                })

            elif algorithm == 'otzhig':
                otzhig_a, otzhig_b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = otzhig.otzhig(tables, table_id)
                table_data = [
                    {'x2': float(x2), 'gmod': float(gmod), 'gexp': float(gexp), 'sigma': float(op), 'delta': float(ap)}
                    for x2, gmod, gexp, op, ap in zip(l_x2, l_gmod, l_gexp, l_op, l_ap)
                ]

                result = CalculationResult.objects.create(
                    user=request.user,
                    title=table.title,
                    algorithm='Метод симуляции отжига',
                    param_a=otzhig_a,
                    param_b=otzhig_b,
                    table=table,  # Передаем объект Table
                    iterations=iterations or 0,
                    average_op=avg_op,
                    exec_time=exec_time,
                    table_data=json.dumps(table_data)  # Сериализуем в JSON
                )

                response_data.update({
                    'i': round(otzhig_a, 3),
                    'j': round(otzhig_b, 3),
                    'iterations': iterations or 'N/A',
                    'exec_time': f"{exec_time:.3f} сек" if exec_time else 'N/A',
                    'table_data': table_data,
                    'result_id': result.id
                })

                context.update({
                    'result': result,  # Передаем результат в шаблон
                    'table_data': table_data  # Передаем данные таблицы в шаблон
                })

            # Сохранение в сессии
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
