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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from .forms import PostForm, CommentForm

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
    """
    Отображает пост (с форума или с графика) + его комментарии.
    Позволяет добавлять новые комментарии.
    """
    post = get_object_or_404(Post, id=post_id)
    calculation_result = getattr(post, 'calculation_result', None)

    # Попробуем извлечь параметры из поста
    lines = post.content.split("\n")
    data_lines = []
    for line in lines:
        if line.strip():
            try:
                parts = line.split(',')
                if len(parts) == 5:
                    x2 = parts[0].strip()
                    gexp = parts[1].strip()
                    gmod = parts[2].strip()
                    sigma = parts[3].strip().replace('%', '')
                    delta = parts[4].strip()

                    try:
                        x2 = str(float(x2))[0:5] if x2 != 'N/A' else '0.000'
                        gexp = float(gexp) if gexp != 'N/A' else 0.0
                        gmod = float(gmod) if gmod != 'N/A' else 0.0
                        sigma = float(sigma) if sigma != 'N/A' else 0.0
                        delta = float(delta) if delta != 'N/A' else 0.0
                    except ValueError:
                        continue

                    data_lines.append({
                        'x2': x2,
                        'gexp': gexp,
                        'gmod': gmod,
                        'sigma': sigma,
                        'delta': delta,
                    })
            except Exception as e:
                print(f"Ошибка обработки строки: {line}, {e}")

    # Извлечение данных о расчёте
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
        result_info = {}
        for line in lines:
            if line.startswith("Параметр A:"):
                result_info['param_a'] = float(line.split(":")[1].strip())
            elif line.startswith("Параметр B:"):
                result_info['param_b'] = float(line.split(":")[1].strip())
            elif line.startswith("Итерации:"):
                try:
                    result_info['iterations'] = int(line.split(":")[1].strip())
                except:
                    result_info['iterations'] = None
            elif line.startswith("Время выполнения:"):
                try:
                    time_str = line.split(":")[1].strip().replace(" сек", "")
                    result_info['exec_time'] = float(time_str)
                except:
                    result_info['exec_time'] = None
            elif line.startswith("Алгоритм:"):
                result_info['algorithm'] = line.split(":")[1].strip()
            elif line.startswith("Средняя погрешность:"):
                try:
                    error_str = line.split(":")[1].strip().replace("%", "")
                    result_info['average_error'] = float(error_str)
                except:
                    result_info['average_error'] = None

    # --- Работа с комментариями ---
    comments = post.comments.all().order_by('-created_at')

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, "Комментарий добавлен!")
            return redirect('forum_detail', post_id=post.id)
    else:
        comment_form = CommentForm()

    return render(request, 'forum_detail.html', {
        'post': post,
        'data_lines': data_lines,
        'result_info': result_info,
        'comments': comments,
        'form': comment_form
    })

@login_required
def forum_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.source = 'forum'

            # Сохраняем технические поля
            post.algorithm = form.cleaned_data.get('algorithm') or ''
            post.a12 = form.cleaned_data.get('a12') or ''
            post.a21 = form.cleaned_data.get('a21') or ''
            post.iterations = form.cleaned_data.get('iterations') or ''
            post.exec_time = form.cleaned_data.get('exec_time') or ''
            post.average_error = form.cleaned_data.get('average_error') or ''

            post.save()
            form.save_m2m()

            messages.success(request, "Пост успешно создан!")
            return redirect('forum_detail', post_id=post.id)
    else:
        form = PostForm(user=request.user)

    return render(request, 'forum_create.html', {'form': form})



@login_required
def forum_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user and request.method == "POST":
        post.delete()
        messages.success(request, "Пост успешно удалён.")
    return redirect('forum_list')


@login_required
def forum_edit(request, pk):
    """Редактирование поста"""
    post = get_object_or_404(Post, pk=pk)

    # Только автор может редактировать
    if post.author != request.user:
        messages.error(request, "Вы не можете редактировать чужой пост.")
        return redirect('forum_list')

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.source = post.source  # сохраняем источник

            post.algorithm = form.cleaned_data.get('algorithm')
            post.a12 = form.cleaned_data.get('a12')
            post.a21 = form.cleaned_data.get('a21')
            post.iterations = form.cleaned_data.get('iterations')
            post.exec_time = form.cleaned_data.get('exec_time')
            post.average_error = form.cleaned_data.get('average_error')

            post.save()
            form.save_m2m()

            messages.success(request, "Пост успешно обновлён!")
            return redirect('forum_detail', post_id=post.pk)

    else:
        form = PostForm(instance=post, user=request.user)

    return render(request, 'forum_edit.html', {'form': form, 'post': post})


@login_required
def share_calculation(request, result_id):
    """Создание поста из расчёта"""
    result = get_object_or_404(CalculationResult, id=result_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.calculation_result = result
            post.source = 'calculation'

            # 💾 Делаем snapshot (копию расчёта)
            post.calculation_snapshot = {
                'param_a': result.param_a,
                'param_b': result.param_b,
                'iterations': result.iterations,
                'exec_time': result.exec_time,
                'algorithm': result.algorithm,
                'average_op': result.average_op,
                'table_data': result.get_table_data(),
                'title': result.title,
            }

            # Автоматически заполняем технические поля
            post.algorithm = result.algorithm or 'Не указан'
            post.a12 = str(result.param_a) if result.param_a is not None else 'N/A'
            post.a21 = str(result.param_b) if result.param_b is not None else 'N/A'
            post.iterations = str(result.iterations) if result.iterations is not None else 'N/A'
            post.exec_time = f"{result.exec_time:.2f} сек" if result.exec_time is not None else 'N/A'
            post.average_error = f"{result.average_op:.1f}%" if result.average_op is not None else 'N/A'

            # Формируем текст поста
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

            content_lines = [
                f"Результат расчета #{result.id}:",
                f"Название: {result.title}",
                f"Параметр A: {result.param_a:.3f}",
                f"Параметр B: {result.param_b:.3f}",
                f"Итерации: {result.iterations if result.iterations is not None else 'N/A'}",
                f"Время выполнения: {result.exec_time:.2f} сек" if result.exec_time else "Время выполнения: N/A",
                f"Алгоритм: {result.algorithm or 'Не указан'}",
                f"Средняя погрешность: {result.average_op:.1f}%" if result.average_op else "Средняя погрешность: N/A",
                "Данные таблицы:",
                table_data_str,
                ""
            ]

            user_content = form.cleaned_data['content'].strip()
            if user_content:
                content_lines.append(user_content)

            post.content = "\n".join(content_lines)
            post.save()

            messages.success(request, 'Результат расчета успешно опубликован на форуме!')
            return redirect('forum_list')

    else:
        initial_data = {
            'title': f'Результат расчета: {result.title}',
            'content': '',
            'algorithm': result.algorithm or 'Не указан',
            'a12': str(result.param_a) if result.param_a is not None else 'N/A',
            'a21': str(result.param_b) if result.param_b is not None else 'N/A',
            'iterations': str(result.iterations) if result.iterations is not None else 'N/A',
            'exec_time': f"{result.exec_time:.2f}" if result.exec_time is not None else 'N/A',
            'average_error': f"{result.average_op:.1f}" if result.average_op is not None else 'N/A',
        }
        form = PostForm(initial=initial_data, user=request.user)

    return render(request, 'forum_create.html', {
        'form': form,
        'result': result,
        'is_from_calculation': True
    })


@login_required
def graph_view(request):
    # Достаём из сессии сохранённые данные
    result_id = request.session.get('result_id')
    table_id = request.session.get('table_id')
    param_a = request.session.get('param_a')
    param_b = request.session.get('param_b')

    initial_data = {}
    result = None

    # Заполняем форму старыми значениями
    if result_id:
        try:
            result = CalculationResult.objects.get(id=result_id)
            initial_data = {
                'table_choice': str(result.table.id),
                'parameter_a': round(result.param_a, 3),
                'parameter_b': round(result.param_b, 3),
            }
        except CalculationResult.DoesNotExist:
            result = None
    else:
        if table_id:
            initial_data['table_choice'] = str(table_id)
        if param_a is not None:
            initial_data['parameter_a'] = round(param_a, 3)
        if param_b is not None:
            initial_data['parameter_b'] = round(param_b, 3)

    form = GraphForm(request.POST or None, initial=initial_data)
    context = {'form': form}

    # POST — строим график
    if request.method == 'POST' and form.is_valid():
        table_id = int(form.cleaned_data['table_choice'])
        table = Table.objects.get(id=table_id)
        parameter_a = float(form.cleaned_data['parameter_a'])
        parameter_b = float(form.cleaned_data['parameter_b'])

        # Сохраняем параметры в сессию
        request.session['table_id'] = table_id
        request.session['param_a'] = parameter_a
        request.session['param_b'] = parameter_b

        # Данные графика
        new_x = np.linspace(0, 1, 1000)
        new_y = []
        xx, yy = [], []

        for point in table.points.all():
            xx.append(point.x_value)
            yy.append(point.y_value)

        for point in new_x:
            x1 = 1 - point
            rt = table.temperature * 8.314462618
            y_value = rt * x1 * point * (x1 * parameter_a + point * parameter_b)
            new_y.append(y_value)

        # Рисуем график
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(new_x, new_y, color='red', markersize=1)
        ax.scatter(xx, yy, color='blue')
        ax.set_title(table.title)
        ax.set_xlabel(r'$x_2$')
        ax.set_ylabel(r'$G^{E}$')
        ax.grid(True)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        plt.close(fig)

        # ✅ Сохраняем график в сессию для скачивания
        request.session['last_graph'] = graphic

        # Таблица ошибок
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

        # Если график из результатов — продолжаем цепочку
        if result:
            request.session['result_id'] = result.id
            context.update({'result_id': result.id, 'graphic_result': result})
        else:
            request.session['result_id'] = None

        context.update({
            'graphic': graphic,
            'a': round(parameter_a, 3),
            'b': round(parameter_b, 3),
            'table_data': table_data
        })

    # Передаём значения для отображения (если не POST)
    if param_a is not None and param_b is not None:
        context.update({'a': round(param_a, 3), 'b': round(param_b, 3)})

    return render(request, 'graphs.html', context)


@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)

@login_required
def delete_result(request, result_id):
    """Удаление расчёта пользователем без потери постов"""
    result = get_object_or_404(CalculationResult, id=result_id)

    if request.user != result.user:
        messages.error(request, "Вы не можете удалить чужой расчёт.")
        return redirect('profile')

    # 💾 Перед удалением — обновляем посты, чтобы сохранить копию данных
    related_posts = Post.objects.filter(calculation_result=result)
    for post in related_posts:
        if not post.calculation_snapshot:
            post.calculation_snapshot = {
                'param_a': result.param_a,
                'param_b': result.param_b,
                'iterations': result.iterations,
                'exec_time': result.exec_time,
                'algorithm': result.algorithm,
                'average_op': result.average_op,
                'table_data': result.get_table_data(),
                'title': result.title,
            }
            post.save(update_fields=['calculation_snapshot'])

    result.delete()
    messages.success(request, "Расчёт удалён. Посты сохранены.")
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

from django.http import HttpResponse
import base64
from io import BytesIO

@login_required
def download_graph(request):
    image_base64 = request.session.get('last_graph')

    if not image_base64:
        messages.error(request, "Сначала постройте график!")
        return redirect('graph_view')

    # декодируем картинку
    image_data = base64.b64decode(image_base64)
    response = HttpResponse(image_data, content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="graph.png"'
    return response


@login_required
def databases(request):
    tables = Table.objects.all()
    context = {"tables": tables}
    return render(request, "databases.html", context)


@login_required
def delete_table(request, pk):
    table = get_object_or_404(Table, pk=pk)

    # Проверка на владельца
    if table.author != request.user:
        messages.error(request, "Вы не можете удалить таблицу, так как вы не являетесь её автором.")
        return redirect("databases")

    # Сохраняем snapshot для связанных расчётов
    results = CalculationResult.objects.filter(table=table)
    if results.exists():
        points_data = [{"x2": p.x_value, "gexp": p.y_value} for p in table.points.all()]
        for res in results:
            if not res.table_data:
                res.table_data = json.dumps(points_data)
                res.save(update_fields=["table_data"])

    table.delete()
    messages.success(request, "Таблица удалена, но расчёты и посты сохранены.")
    return redirect("databases")


@login_required
def create_table(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        rows = data.strip().split('\n')
        temperature = float(rows[-1])
        title = rows[0]
        solution = rows[1]

        # Привязка к текущему пользователю
        table = Table.objects.create(
            temperature=temperature,
            title=title,
            solution=solution,
            author=request.user
        )

        for row in rows[2:-1]:
            x_value, y_value = map(float, row.split(';'))
            point = Point.objects.create(x_value=x_value, y_value=y_value)
            table.points.add(point)

        return HttpResponseRedirect('/databases/')

    return render(request, 'create_table.html')
