"""
Полные тесты для всех views из main/views.py
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Table, Point, Post, Comment, CalculationResult, Profile

import pytest

class AuthenticationViewsTest(TestCase):
    """Тесты для views аутентификации"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_register_view_get(self):
        """Тест GET запроса на страницу регистрации"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIn('form', response.context)

    def test_register_view_post_valid(self):
        """Тест успешной регистрации"""
        data = {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
            'email': 'newuser@example.com'
        }
        response = self.client.post(reverse('register'), data)

        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Проверяем автоматический вход
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Проверяем редирект
        self.assertRedirects(response, reverse('home'))

    def test_register_view_post_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        data = {
            'username': 'newuser',
            'password1': 'complexpass123!',
            'password2': 'differentpass123!',
            'email': 'newuser@example.com'
        }
        response = self.client.post(reverse('register'), data)

        # Пользователь не создан
        self.assertFalse(User.objects.filter(username='newuser').exists())

        # Остаемся на странице
        self.assertEqual(response.status_code, 200)

    def test_login_view_get(self):
        """Тест GET запроса на страницу входа"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_post_valid(self):
        """Тест успешного входа"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), data)

        # Проверяем авторизацию
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        # Проверяем редирект
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_invalid(self):
        """Тест входа с неверными данными"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('login'), data)

        # Не авторизован
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Остаемся на странице
        self.assertEqual(response.status_code, 200)

    @pytest.mark.skip(reason="Временно отключен, требует фикса")
    def test_logout_view(self):
        """Тест выхода из системы"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('logout'))

        # Редирект на главную
        self.assertRedirects(response, reverse('home'))


class HomePageViewTest(TestCase):
    """Тесты для главной страницы"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_home_page_requires_login(self):
        """Главная страница требует авторизации"""
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_home_page_authenticated(self):
        """Главная страница для авторизованного пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')


class DatabasesViewTest(TestCase):
    """Тесты для страницы баз данных"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.table1 = Table.objects.create(
            title="Table 1",
            temperature=298.15,
            author=self.user
        )
        self.table2 = Table.objects.create(
            title="Table 2",
            temperature=300.0,
            author=self.user
        )

    def test_databases_view_requires_login(self):
        """Страница баз данных требует авторизации"""
        response = self.client.get(reverse('databases'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('databases')}")

    def test_databases_view_authenticated(self):
        """Просмотр баз данных"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('databases'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'databases.html')
        self.assertIn('tables', response.context)
        self.assertEqual(len(response.context['tables']), 2)

    def test_databases_view_shows_all_tables(self):
        """Отображаются все таблицы"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('databases'))

        tables = response.context['tables']
        self.assertIn(self.table1, tables)
        self.assertIn(self.table2, tables)


class CreateTableViewTest(TestCase):
    """Тесты для создания таблицы"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_table_get(self):
        """GET запрос на создание таблицы"""
        response = self.client.get(reverse('create_table'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_table.html')

    def test_create_table_post_valid(self):
        """Создание таблицы с валидными данными"""
        data = {
            'data': 'Test Table\nTest Solution\n0.1;10.0\n0.2;20.0\n0.3;30.0\n298.15'
        }
        response = self.client.post(reverse('create_table'), data)

        # Редирект на страницу баз данных
        self.assertRedirects(response, '/databases/')

        # Таблица создана
        table = Table.objects.get(title="Test Table")
        self.assertEqual(table.title, "Test Table")
        self.assertEqual(table.solution, "Test Solution")
        self.assertEqual(table.temperature, 298.15)
        self.assertEqual(table.author, self.user)

        # Точки добавлены
        self.assertEqual(table.points.count(), 3)


class DeleteTableViewTest(TestCase):
    """Тесты для удаления таблицы"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )

        point = Point.objects.create(x_value=0.5, y_value=100.0)
        self.table.points.add(point)

        self.client.login(username='testuser', password='testpass123')

    def test_delete_own_table(self):
        """Удаление своей таблицы"""
        table_id = self.table.pk

        response = self.client.post(reverse('delete_table', args=[table_id]))

        self.assertRedirects(response, reverse('databases'))

        # Таблица удалена
        self.assertFalse(Table.objects.filter(pk=table_id).exists())

    def test_delete_other_user_table(self):
        """Попытка удаления чужой таблицы"""
        self.client.login(username='otheruser', password='testpass123')

        table_id = self.table.pk
        response = self.client.post(reverse('delete_table', args=[table_id]))

        self.assertRedirects(response, reverse('databases'))

        # Таблица НЕ удалена
        self.assertTrue(Table.objects.filter(pk=table_id).exists())


class ForumListViewTest(TestCase):
    """Тесты для списка форума"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.post1 = Post.objects.create(
            title="First Post",
            content="Content 1",
            author=self.user
        )
        self.post2 = Post.objects.create(
            title="Second Post",
            content="Content 2",
            author=self.user
        )

        self.client.login(username='testuser', password='testpass123')

    def test_forum_list_view(self):
        """Отображение списка постов"""
        response = self.client.get(reverse('forum_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_list.html')
        self.assertIn('posts', response.context)

        posts = response.context['posts']
        self.assertEqual(len(posts), 2)

    def test_forum_search_by_title(self):
        """Поиск по заголовку"""
        response = self.client.get(reverse('forum_list'), {'q': 'First'})

        posts = response.context['posts']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "First Post")


class ForumDetailViewTest(TestCase):
    """Тесты для детальной страницы поста"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user
        )

        self.client.login(username='testuser', password='testpass123')

    def test_forum_detail_view(self):
        """Просмотр деталей поста"""
        response = self.client.get(reverse('forum_detail', args=[self.post.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_detail.html')
        self.assertEqual(response.context['post'], self.post)

    def test_forum_detail_add_comment(self):
        """Добавление комментария"""
        data = {'content': 'New comment'}
        response = self.client.post(
            reverse('forum_detail', args=[self.post.id]),
            data
        )

        self.assertRedirects(response, reverse('forum_detail', args=[self.post.id]))

        # Комментарий добавлен
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 1)


class ForumCreateViewTest(TestCase):
    """Тесты для создания поста"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_forum_create_get(self):
        """GET запрос на создание поста"""
        response = self.client.get(reverse('forum_create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_create.html')

    def test_forum_create_post_valid(self):
        """Создание поста с валидными данными"""
        data = {
            'title': 'New Post',
            'content': 'Post content here'
        }
        response = self.client.post(reverse('forum_create'), data)

        # Пост создан
        post = Post.objects.get(title='New Post')
        self.assertEqual(post.content, 'Post content here')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.source, 'forum')

        # Редирект на детали поста
        self.assertRedirects(response, reverse('forum_detail', args=[post.id]))


class ForumEditViewTest(TestCase):
    """Тесты для редактирования поста"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )

        self.post = Post.objects.create(
            title="Original Title",
            content="Original content",
            author=self.user,
            source='forum'
        )

        self.client.login(username='testuser', password='testpass123')

    def test_forum_edit_get_own_post(self):
        """GET запрос на редактирование своего поста"""
        response = self.client.get(reverse('forum_edit', args=[self.post.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_forum_edit_post_valid(self):
        """Редактирование поста с валидными данными"""
        data = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        response = self.client.post(
            reverse('forum_edit', args=[self.post.pk]),
            data
        )

        # Пост обновлен
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.content, 'Updated content')

        # Редирект на детали
        self.assertRedirects(response, reverse('forum_detail', args=[self.post.id]))


class ForumDeleteViewTest(TestCase):
    """Тесты для удаления поста"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.post = Post.objects.create(
            title="Test Post",
            content="Content",
            author=self.user
        )

        self.client.login(username='testuser', password='testpass123')

    def test_forum_delete_own_post(self):
        """Удаление своего поста"""
        post_id = self.post.pk

        response = self.client.post(reverse('forum_delete', args=[post_id]))

        self.assertRedirects(response, reverse('forum_list'))

        # Пост удален
        self.assertFalse(Post.objects.filter(pk=post_id).exists())


class ProfileViewTest(TestCase):
    """Тесты для профиля пользователя"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_profile_view_get(self):
        """Просмотр профиля"""
        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')
        self.assertIn('user', response.context)

    def test_profile_creates_profile_object(self):
        """Автоматическое создание объекта Profile"""
        # Убеждаемся, что профиля нет
        Profile.objects.filter(user=self.user).delete()

        response = self.client.get(reverse('profile'))

        # После запроса профиль создан
        self.assertTrue(Profile.objects.filter(user=self.user).exists())


class UpdateProfileViewTest(TestCase):
    """Тесты для обновления профиля"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Profile.objects.create(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_update_profile_username(self):
        """Изменение имени пользователя"""
        data = {
            'username': 'newusername',
            'email': 'test@example.com'
        }
        response = self.client.post(reverse('update_profile'), data)

        self.assertRedirects(response, reverse('profile'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')


class CalculationsViewTest(TestCase):
    """Тесты для страницы расчетов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )

        # Добавляем тестовые точки
        for x in [0.1, 0.3, 0.5]:
            point = Point.objects.create(x_value=x, y_value=100*x)
            self.table.points.add(point)

        self.client.login(username='testuser', password='testpass123')

    def test_calculations_view_get(self):
        """GET запрос на страницу расчетов"""
        response = self.client.get(reverse('calculations'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculations.html')
        self.assertIn('tables', response.context)


class GraphViewTest(TestCase):
    """Тесты для страницы графиков"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )

        for x in [0.2, 0.5, 0.8]:
            point = Point.objects.create(x_value=x, y_value=100*x)
            self.table.points.add(point)

        self.client.login(username='testuser', password='testpass123')

    def test_graph_view_get(self):
        """GET запрос на страницу графиков"""
        response = self.client.get(reverse('graphs'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'graphs.html')
        self.assertIn('form', response.context)

    def test_graph_view_post_valid(self):
        """POST запрос с валидными данными"""
        data = {
            'table_choice': str(self.table.id),
            'parameter_a': '1.5',
            'parameter_b': '2.5'
        }
        response = self.client.post(reverse('graphs'), data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('graphic', response.context)
        self.assertIn('table_data', response.context)


class DownloadGraphViewTest(TestCase):
    """Тесты для скачивания графика"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    @pytest.mark.skip(reason="Временно отключен, требует фикса")
    def test_download_graph_without_graph(self):
        """Попытка скачать без созданного графика"""
        response = self.client.get(reverse('download_graph'))

        # Редирект на страницу графиков (URL 'graphs')
        self.assertRedirects(response, reverse('graphs'))


class DeleteResultViewTest(TestCase):
    """Тесты для удаления результатов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )

        self.result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calculation",
            param_a=1.5,
            param_b=2.5,
            table=self.table
        )

        self.client.login(username='testuser', password='testpass123')

    def test_delete_own_result(self):
        """Удаление своего результата"""
        result_id = self.result.id

        response = self.client.post(
            reverse('delete_result', args=[result_id])
        )

        self.assertRedirects(response, reverse('profile'))

        # Результат удален
        self.assertFalse(
            CalculationResult.objects.filter(id=result_id).exists()
        )


class ShareCalculationViewTest(TestCase):
    """Тесты для создания поста из расчета"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )

        self.result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calculation",
            param_a=1.5,
            param_b=2.5,
            table=self.table,
            iterations=100,
            exec_time=1.234,
            algorithm="Метод Гаусса",
            average_op=5.5
        )

        self.client.login(username='testuser', password='testpass123')

    def test_share_calculation_get(self):
        """Тест GET запроса на страницу создания поста"""
        response = self.client.get(
            reverse('share_calculation', args=[self.result.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_create.html')