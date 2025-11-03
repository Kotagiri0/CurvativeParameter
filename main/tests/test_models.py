import json
from django.test import TestCase
from django.contrib.auth.models import User
from main.models import Point, Table, CalculationResult, Profile, Post, Comment


class PointModelTest(TestCase):
    """Тесты для модели Point"""

    def setUp(self):
        self.point = Point.objects.create(x_value=0.5, y_value=100.5)

    def test_point_creation(self):
        """Проверка создания точки"""
        self.assertEqual(self.point.x_value, 0.5)
        self.assertEqual(self.point.y_value, 100.5)

    def test_point_str(self):
        """Проверка строкового представления"""
        self.assertEqual(str(self.point), "0.5, 100.5")


class TableModelTest(TestCase):
    """Тесты для модели Table"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.point1 = Point.objects.create(x_value=0.1, y_value=10.0)
        self.point2 = Point.objects.create(x_value=0.2, y_value=20.0)
        self.table = Table.objects.create(
            title="Test Table",
            solution="Test Solution",
            temperature=298.15,
            author=self.user
        )
        self.table.points.add(self.point1, self.point2)

    def test_table_creation(self):
        """Проверка создания таблицы"""
        self.assertEqual(self.table.title, "Test Table")
        self.assertEqual(self.table.temperature, 298.15)
        self.assertEqual(self.table.author, self.user)

    def test_table_points_relationship(self):
        """Проверка связи с точками"""
        self.assertEqual(self.table.points.count(), 2)
        self.assertIn(self.point1, self.table.points.all())
        self.assertIn(self.point2, self.table.points.all())

    def test_table_str(self):
        """Проверка строкового представления"""
        self.assertEqual(str(self.table), "Test Table")


class CalculationResultModelTest(TestCase):
    """Тесты для модели CalculationResult"""

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
            title="Test Calculation",
            param_a=1.5,
            param_b=2.5,
            table=self.table,
            iterations=100,
            exec_time=1.23,
            algorithm="Gauss",
            average_op=5.5,
            table_data=json.dumps([
                {"x2": 0.1, "gexp": 10.0, "gmod": 10.5, "sigma": 5.0, "delta": 0.5}
            ])
        )

    def test_calculation_creation(self):
        """Проверка создания расчета"""
        self.assertEqual(self.result.user, self.user)
        self.assertEqual(self.result.title, "Test Calculation")
        self.assertEqual(self.result.param_a, 1.5)
        self.assertEqual(self.result.param_b, 2.5)

    def test_get_table_data(self):
        """Проверка метода get_table_data"""
        data = self.result.get_table_data()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['x2'], 0.1)

    def test_calculation_str(self):
        """Проверка строкового представления"""
        expected = f"Calculation #{self.result.id} by testuser"
        self.assertEqual(str(self.result), expected)

    def test_calculation_without_table(self):
        """Проверка создания расчета без таблицы"""
        result2 = CalculationResult.objects.create(
            user=self.user,
            title="No Table Calc",
            param_a=1.0,
            param_b=1.0
        )
        self.assertIsNone(result2.table)


class ProfileModelTest(TestCase):
    """Тесты для модели Profile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = Profile.objects.create(user=self.user)

    def test_profile_creation(self):
        """Проверка создания профиля"""
        self.assertEqual(self.profile.user, self.user)

    def test_profile_str(self):
        """Проверка строкового представления"""
        self.assertEqual(str(self.profile), "Profile of testuser")


class PostModelTest(TestCase):
    """Тесты для модели Post"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.user,
            source='forum'
        )

    def test_post_creation(self):
        """Проверка создания поста"""
        self.assertEqual(self.post.title, "Test Post")
        self.assertEqual(self.post.content, "Test content")
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.source, 'forum')

    def test_post_str(self):
        """Проверка строкового представления"""
        self.assertEqual(str(self.post), "Test Post")

    def test_is_from_calculation_property(self):
        """Проверка свойства is_from_calculation"""
        self.assertFalse(self.post.is_from_calculation)

        calc_post = Post.objects.create(
            title="Calc Post",
            content="Calc content",
            author=self.user,
            source='calculation'
        )
        self.assertTrue(calc_post.is_from_calculation)

    def test_post_with_calculation_result(self):
        """Проверка поста с результатом расчета"""
        table = Table.objects.create(
            title="Test Table",
            temperature=298.15,
            author=self.user
        )
        result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calc",
            param_a=1.0,
            param_b=1.0,
            table=table
        )
        post = Post.objects.create(
            title="Calc Post",
            content="Content",
            author=self.user,
            calculation_result=result,
            source='calculation'
        )
        self.assertEqual(post.calculation_result, result)


class CommentModelTest(TestCase):
    """Тесты для модели Comment"""

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
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Test comment"
        )

    def test_comment_creation(self):
        """Проверка создания комментария"""
        self.assertEqual(self.comment.post, self.post)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, "Test comment")

    def test_comment_str(self):
        """Проверка строкового представления"""
        expected = f"Комментарий от testuser к 'Test Post'"
        self.assertEqual(str(self.comment), expected)

    def test_comment_ordering(self):
        """Проверка сортировки комментариев"""
        comment2 = Comment.objects.create(
            post=self.post,
            author=self.user,
            content="Second comment"
        )
        comments = Comment.objects.all()
        self.assertEqual(comments[0], comment2)  # Новые комментарии первыми