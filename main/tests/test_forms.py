from django.test import TestCase
from django.contrib.auth.models import User
from main.forms import (
    RegisterForm, LoginForm, GraphForm,
    UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm
)
from main.models import Table, Point, CalculationResult, Profile, Post


class RegisterFormTest(TestCase):
    """Тесты для формы регистрации"""

    def test_valid_form(self):
        """Тест валидной формы регистрации"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Тест несовпадения паролей"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complexpass123!',
            'password2': 'differentpass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_username_already_exists(self):
        """Тест существующего имени пользователя"""
        User.objects.create_user(username='existinguser', password='pass123')
        form_data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password1': 'complexpass123!',
            'password2': 'complexpass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())


class LoginFormTest(TestCase):
    """Тесты для формы входа"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_valid_login(self):
        """Тест валидной формы входа"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123',
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_password(self):
        """Тест неверного пароля"""
        form_data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())


class GraphFormTest(TestCase):
    """Тесты для формы графиков"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.point = Point.objects.create(x_value=0.5, y_value=100.0)
        self.table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )
        self.table.points.add(self.point)

    def test_valid_form(self):
        """Тест валидной формы графиков"""
        form_data = {
            'table_choice': str(self.table.id),
            'parameter_a': 1.5,
            'parameter_b': 2.5,
        }
        form = GraphForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_parameters(self):
        """Тест невалидных параметров"""
        form_data = {
            'table_choice': str(self.table.id),
            'parameter_a': 'invalid',
            'parameter_b': 2.5,
        }
        form = GraphForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_missing_table(self):
        """Тест отсутствующей таблицы"""
        form_data = {
            'table_choice': '',
            'parameter_a': 1.5,
            'parameter_b': 2.5,
        }
        form = GraphForm(data=form_data)
        self.assertFalse(form.is_valid())


class UserUpdateFormTest(TestCase):
    """Тесты для формы обновления пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_update(self):
        """Тест валидного обновления"""
        form_data = {
            'username': 'updateduser',
            'email': 'updated@example.com',
        }
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        """Тест невалидного email"""
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email',
        }
        form = UserUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())


class ProfileUpdateFormTest(TestCase):
    """Тесты для формы обновления профиля"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(user=self.user)

    def test_valid_form(self):
        """Тест валидной формы профиля"""
        form = ProfileUpdateForm(instance=self.profile)
        self.assertIsNotNone(form)


class PostFormTest(TestCase):
    """Тесты для формы постов"""

    def setUp(self):
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
            title="Test Calc",
            param_a=1.0,
            param_b=1.0,
            table=self.table
        )

    def test_valid_forum_post(self):
        """Тест валидного поста с форума"""
        form_data = {
            'title': 'Test Post',
            'content': 'Test content for the post',
        }
        form = PostForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_empty_title(self):
        """Тест пустого заголовка"""
        form_data = {
            'title': '',
            'content': 'Test content',
        }
        form = PostForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_empty_content(self):
        """Тест пустого содержания"""
        form_data = {
            'title': 'Test Post',
            'content': '',
        }
        form = PostForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_post_with_calculation(self):
        """Тест поста с результатом расчета"""
        form_data = {
            'title': 'Calculation Post',
            'content': 'Post with calculation',
            'calculation_result': self.result.id,
        }
        form = PostForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())


class CommentFormTest(TestCase):
    """Тесты для формы комментариев"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user
        )

    def test_valid_comment(self):
        """Тест валидного комментария"""
        form_data = {
            'content': 'This is a test comment',
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_empty_comment(self):
        """Тест пустого комментария"""
        form_data = {
            'content': '',
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_long_comment(self):
        """Тест слишком длинного комментария"""
        form_data = {
            'content': 'x' * 1001,  # Максимум 1000 символов
        }
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_max_length_comment(self):
        """Тест комментария максимальной длины"""
        form_data = {
            'content': 'x' * 1000,  # Ровно 1000 символов
        }
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())