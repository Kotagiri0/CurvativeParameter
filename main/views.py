import base64
import json
import traceback
from datetime import time
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import (
    RegisterForm, LoginForm, GraphForm, UserUpdateForm,
    ProfileUpdateForm, PostForm, CommentForm
)
from .models import Point, Table, CalculationResult, Profile, Post, Comment
from . import gauss, gauss_step, gradient, gradient_step, otzhig


# === ФОРУМ ===
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
    calculation_result = getattr(post, 'calculation_result', None)

    # Парсинг данных таблицы из контента
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
                        x2 = str(float(x2))[:5] if x2 != 'N/A' else '0.000'
                        gexp = float(gexp) if gexp != 'N/A' else 0.0
                        gmod = float(gmod) if gmod != 'N/A' else 0.0
                        sigma = float(sigma) if sigma != 'N/A' else 0.0
                        delta = float(delta) if delta != 'N/A' else 0.0
                    except ValueError:
                        continue
                    data_lines.append({
                        'x2': x2, 'gexp': gexp, 'gmod': gmod,
                        'sigma': sigma, 'delta': delta,
                    })
            except Exception as e:
                print(f"Ошибка обработки строки: {line}, {e}")

    # Извлечение метаданных
    result_info = {}
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
        for line in lines:
            if line.startswith("Параметр A:"):
                result_info['param_a'] = float(line.split(":")[1].strip())
            elif line.startswith("Параметр B:"):
                result_info['param_b'] = float(line.split(":")[1].strip())
            elif line.startswith("Итерации:"):
                try: result_info['iterations'] = int(line.split(":")[1].strip())
                except: result_info['iterations'] = None
            elif line.startswith("Время выполнения:"):
                try:
                    time_str = line.split(":")[1].strip().replace(" сек", "")
                    result_info['exec_time'] = float(time_str)
                except: result_info['exec_time'] = None
            elif line.startswith("Алгоритм:"):
                result_info['algorithm'] = line.split(":")[1].strip()
            elif line.startswith("Средняя погрешность:"):
                try:
                    error_str = line.split(":")[1].strip().replace("%", "")
                    result_info['average_error'] = float(error_str)
                except: result_info['average_error'] = None

    # Комментарии
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





# === ГРАФИК ===
@login_required
def graph_view(request):
    result_id = request.session.get('result_id')
    table_id = request.session.get('table_id')
    param_a = request.session.get('param_a')
    param_b = request.session.get('param_b')
    initial_data = {}
    result = None

    if result_id:
        try:
            result = CalculationResult.objects.get(id=result_id)
            table_choice = str(result.table.id) if result.table else None
            initial_data = {
                'table_choice': table_choice,
                'parameter_a': round(result.param_a, 3) if result.param_a is not None else '',
                'parameter_b': round(result.param_b, 3) if result.param_b is not None else '',
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
    is_post = False

    if request.method == 'POST' and form.is_valid():
        is_post = True
        table_id = int(form.cleaned_data['table_choice'])
        table = Table.objects.get(id=table_id)
        parameter_a = float(form.cleaned_data['parameter_a'])
        parameter_b = float(form.cleaned_data['parameter_b'])

        request.session['table_id'] = table_id
        request.session['param_a'] = parameter_a
        request.session['param_b'] = parameter_b

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

        request.session['last_graph'] = graphic

        table_data = []
        for x, y_exp in zip(xx, yy):
            x1 = 1 - x
            rt = table.temperature * 8.314462618
            y_mod = rt * x1 * x * (x1 * parameter_a + x * parameter_b)
            delta = abs(y_exp - y_mod)
            sigma = (delta / y_exp * 100) if y_exp != 0 else 0
            table_data.append({
                "x2": x, "gmod": y_mod, "gexp": y_exp,
                "sigma": sigma, "delta": delta
            })

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

    if not is_post and param_a is not None and param_b is not None:
        context.update({'a': round(param_a, 3), 'b': round(param_b, 3)})

    return render(request, 'graphs.html', context)


@login_required
def download_graph(request):
    image_base64 = request.session.get('last_graph')
    if not image_base64:
        messages.error(request, "Сначала постройте график!")
        return redirect('graph_view')
    image_data = base64.b64decode(image_base64)
    response = HttpResponse(image_data, content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="graph.png"'
    return response


# === БАЗЫ ДАННЫХ ===
@login_required
def databases(request):
    tables = Table.objects.all()
    return render(request, "databases.html", {"tables": tables})


@login_required
def delete_table(request, pk):
    table = get_object_or_404(Table, pk=pk)
    if table.author != request.user:
        messages.error(request, "Вы не можете удалить таблицу, так как вы не являетесь её автором.")
        return redirect("databases")

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
        table = Table.objects.create(
            temperature=temperature, title=title, solution=solution, author=request.user
        )
        for row in rows[2:-1]:
            x_value, y_value = map(float, row.split(';'))
            point = Point.objects.create(x_value=x_value, y_value=y_value)
            table.points.add(point)
        return HttpResponseRedirect('/databases/')
    return render(request, 'create_table.html')


# === ФОРУМ ===
@login_required
def share_calculation(request, result_id):
    result = get_object_or_404(CalculationResult, id=result_id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.calculation_result = result
            post.source = 'calculation'

            # Snapshot
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

            # Заполнение технических полей
            post.algorithm = result.algorithm or 'Не указан'
            post.a12 = str(result.param_a) if result.param_a is not None else 'N/A'
            post.a21 = str(result.param_b) if result.param_b is not None else 'N/A'
            post.iterations = str(result.iterations) if result.iterations is not None else 'N/A'
            post.exec_time = f"{result.exec_time:.2f} сек" if result.exec_time is not None else 'N/A'
            post.average_error = f"{result.average_op:.1f}%" if result.average_op is not None else 'N/A'

            # ВАЖНО: Сохраняем только пользовательский комментарий в content
            user_content = form.cleaned_data['content'].strip()
            post.content = user_content  # Только комментарий пользователя

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
        'form': form, 'result': result, 'is_from_calculation': True
    })


@login_required
def forum_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.error(request, "Вы не можете редактировать чужие посты.")
        return redirect('forum_list')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            # Для постов из расчётов - обновляем только content (описание)
            if post.source == 'calculation':
                post.content = form.cleaned_data['content'].strip()

            # Обновление технических полей (если они были изменены)
            post.algorithm = form.cleaned_data.get('algorithm') or post.algorithm or ''
            post.a12 = form.cleaned_data.get('a12') or post.a12 or ''
            post.a21 = form.cleaned_data.get('a21') or post.a21 or ''
            post.iterations = form.cleaned_data.get('iterations') or post.iterations or ''
            post.exec_time = form.cleaned_data.get('exec_time') or post.exec_time or ''
            post.average_error = form.cleaned_data.get('average_error') or post.average_error or ''

            post.save()
            messages.success(request, "Пост успешно обновлён!")
            return redirect('forum_detail', post_id=post.id)
    else:
        # Для редактирования постов из расчётов - показываем только content
        initial_data = {
            'title': post.title,
            'content': post.content,  # Это уже чистый комментарий
            'algorithm': post.algorithm or '',
            'a12': post.a12 or '',
            'a21': post.a21 or '',
            'iterations': post.iterations or '',
            'exec_time': post.exec_time or '',
            'average_error': post.average_error or '',
        }
        if post.calculation_result:
            initial_data['calculation_result'] = post.calculation_result.id
        form = PostForm(instance=post, initial=initial_data, user=request.user)

    template = 'forum_edit.html' if post.source == 'calculation' else 'forum_edit_coeffs.html'
    return render(request, template, {'form': form, 'post': post})


@login_required
def delete_result(request, result_id):
    result = get_object_or_404(CalculationResult, id=result_id)
    if request.user != result.user:
        messages.error(request, "Вы не можете удалить чужой расчёт.")
        return redirect('profile')

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
            # content уже содержит только пользовательский комментарий
            post.save(update_fields=['calculation_snapshot'])

    result.delete()
    messages.success(request, "Расчёт удалён. Посты сохранены.")
    return redirect('profile')


@login_required
def profile(request):
    Profile.objects.get_or_create(user=request.user)
    user_results = CalculationResult.objects.filter(user=request.user).order_by('-created_at')
    context = {'user_results': user_results}

    if request.method == 'POST':
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
    })
    return render(request, 'profile.html', context)


@login_required
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        avatar = request.FILES.get('avatar')
        user = request.user

        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, 'Имя пользователя уже занято.')
            return redirect('profile')
        if User.objects.exclude(pk=user.pk).filter(email=email).exists():
            messages.error(request, 'Электронная почта уже используется.')
            return redirect('profile')

        user.username = username
        user.email = email
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        if avatar:
            profile.avatar = avatar
            profile.save()
        messages.success(request, 'Профиль успешно обновлен.')
    return redirect('profile')


@login_required
def calculations(request):
    tables = Table.objects.all()
    context = {"tables": tables}

    if request.method == 'POST':
        try:
            algorithm = request.POST.get('algorithm')
            table_id = int(request.POST.get('tabledata')) - 1
            table = tables[table_id]
            response_data = {
                'algorithm': algorithm,
                'iterations': 'N/A',
                'exec_time': 'N/A',
                'table_data': []
            }

            if algorithm == 'gauss':
                a, b, it, t, x2, gmod, gexp, op, ap, avg = gauss.gauss(tables, table_id)
                key_a, key_b = 'a', 'b'
                alg_name = 'Метод Гаусса'
            elif algorithm == 'gauss_step':
                a, b, it, t, x2, gmod, gexp, op, ap, avg = gauss_step.gauss_step(tables, table_id)
                key_a, key_b = 'c', 'd'
                alg_name = 'Метод Гаусса с переменным шагом'
            elif algorithm == 'gradient':
                a, b, it, t, x2, gmod, gexp, op, ap, avg = gradient.gradient(tables, table_id)
                key_a, key_b = 'e', 'f'
                alg_name = 'Метод градиентного спуска'
            elif algorithm == 'gradient_step':
                a, b, it, t, x2, gmod, gexp, op, ap, avg = gradient_step.gradient_step(tables, table_id)
                key_a, key_b = 'g', 'h'
                alg_name = 'Метод градиентного спуска с переменным шагом'
            elif algorithm == 'otzhig':
                a, b, it, t, x2, gmod, gexp, op, ap, avg = otzhig.otzhig(tables, table_id)
                key_a, key_b = 'i', 'j'
                alg_name = 'Метод симуляции отжига'
            else:
                raise ValueError("Неизвестный алгоритм")

            table_data = [
                {'x2': float(x), 'gmod': float(m), 'gexp': float(e), 'sigma': float(o), 'delta': float(d)}
                for x, m, e, o, d in zip(x2, gmod, gexp, op, ap)
            ]

            result = CalculationResult.objects.create(
                user=request.user,
                title=table.title,
                algorithm=alg_name,
                param_a=a, param_b=b,
                table=table,
                iterations=it or 0,
                average_op=avg,
                exec_time=t,
                table_data=json.dumps(table_data)
            )

            response_data.update({
                key_a: round(a, 3), key_b: round(b, 3),
                'iterations': it or 'N/A',
                'exec_time': f"{t:.3f} сек" if t else 'N/A',
                'table_data': table_data,
                'result_id': result.id
            })

            request.session['param_a'] = a
            request.session['param_b'] = b
            request.session['result_id'] = result.id
            request.session['table_choice'] = table_id
            request.session.modified = True

            context.update({'result': result, 'table_data': table_data})
            return JsonResponse(response_data)

        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'error': f'Ошибка: {str(e)}', 'reload': True}, status=500)

    return render(request, 'calculations.html', context)


# === АУТЕНТИФИКАЦИЯ ===
@login_required
def home_page(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
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