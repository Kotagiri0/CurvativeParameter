"""
Расширенные тесты для views с расчетами и графиками
"""
import json
import base64
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Table, Point, CalculationResult, Post, Comment
from io import BytesIO
from PIL import Image


class CalculationsViewExtendedTest(TestCase):
    """Расширенные тесты для страницы расчетов"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Создаем таблицу с реальными данными
        self.table = Table.objects.create(
            title="1-Chlorobutane(1) + Ethanol(2)",
            solution="Test Solution",
            temperature=278.15,
            author=self.user
        )

        # Добавляем тестовые точки
        test_data = [
            (0.0697, 407), (0.0960, 523), (0.1038, 554),
            (0.1312, 634), (0.1325, 659), (0.2160, 888),
        ]

        for x, y in test_data:
            point = Point.objects.create(x_value=x, y_value=y)
            self.table.points.add(point)

        self.client.login(username='testuser', password='testpass123')

    def test_calculations_view_post_gauss(self):
        """Тест POST запроса с алгоритмом Гаусса"""
        data = {
            'algorithm': 'gauss',
            'tabledata': '1'  # ID таблицы начинается с 1
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()

        # Проверяем структуру ответа
        self.assertIn('algorithm', json_data)
        self.assertIn('a', json_data)
        self.assertIn('b', json_data)
        self.assertIn('iterations', json_data)
        self.assertIn('exec_time', json_data)
        self.assertIn('table_data', json_data)
        self.assertIn('result_id', json_data)

        # Проверяем, что результат сохранен в БД
        result = CalculationResult.objects.get(id=json_data['result_id'])
        self.assertEqual(result.algorithm, 'Метод Гаусса')
        self.assertEqual(result.user, self.user)
        self.assertIsNotNone(result.param_a)
        self.assertIsNotNone(result.param_b)

    def test_calculations_view_post_gauss_step(self):
        """Тест POST запроса с алгоритмом Гаусса с переменным шагом"""
        data = {
            'algorithm': 'gauss_step',
            'tabledata': '1'
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()

        self.assertEqual(json_data['algorithm'], 'gauss_step')
        self.assertIn('c', json_data)
        self.assertIn('d', json_data)

        result = CalculationResult.objects.get(id=json_data['result_id'])
        self.assertEqual(result.algorithm, 'Метод Гаусса с переменным шагом')

    def test_calculations_view_post_gradient(self):
        """Тест POST запроса с алгоритмом градиентного спуска"""
        data = {
            'algorithm': 'gradient',
            'tabledata': '1'
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()

        self.assertEqual(json_data['algorithm'], 'gradient')
        self.assertIn('e', json_data)
        self.assertIn('f', json_data)

        result = CalculationResult.objects.get(id=json_data['result_id'])
        self.assertEqual(result.algorithm, 'Метод градиентного спуска')

    def test_calculations_view_post_gradient_step(self):
        """Тест POST запроса с алгоритмом градиентного спуска с переменным шагом"""
        data = {
            'algorithm': 'gradient_step',
            'tabledata': '1'
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()

        self.assertEqual(json_data['algorithm'], 'gradient_step')
        self.assertIn('g', json_data)
        self.assertIn('h', json_data)

        result = CalculationResult.objects.get(id=json_data['result_id'])
        self.assertEqual(result.algorithm, 'Метод градиентного спуска с переменным шагом')

    def test_calculations_view_post_otzhig(self):
        """Тест POST запроса с алгоритмом симуляции отжига"""
        data = {
            'algorithm': 'otzhig',
            'tabledata': '1'
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 200)
        json_data = response.json()

        self.assertEqual(json_data['algorithm'], 'otzhig')
        self.assertIn('i', json_data)
        self.assertIn('j', json_data)

        result = CalculationResult.objects.get(id=json_data['result_id'])
        self.assertEqual(result.algorithm, 'Метод симуляции отжига')

    def test_calculations_session_storage(self):
        """Тест сохранения данных в сессии"""
        data = {
            'algorithm': 'gauss',
            'tabledata': '1'
        }
        response = self.client.post(reverse('calculations'), data)
        json_data = response.json()

        # Проверяем, что данные сохранены в сессии
        session = self.client.session
        self.assertIn('param_a', session)
        self.assertIn('param_b', session)
        self.assertIn('result_id', session)
        self.assertEqual(session['result_id'], json_data['result_id'])

    def test_calculations_invalid_table(self):
        """Тест с несуществующей таблицей"""
        data = {
            'algorithm': 'gauss',
            'tabledata': '999'
        }
        response = self.client.post(reverse('calculations'), data)

        self.assertEqual(response.status_code, 500)
        json_data = response.json()
        self.assertIn('error', json_data)


class GraphViewExtendedTest(TestCase):
    """Расширенные тесты для страницы графиков"""

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

        # Добавляем точки
        for x in [0.1, 0.3, 0.5, 0.7, 0.9]:
            y = 100 * x * (1 - x)  # Простая функция
            point = Point.objects.create(x_value=x, y_value=y)
            self.table.points.add(point)

        self.client.login(username='testuser', password='testpass123')

    def test_graph_view_post_valid(self):
        """Тест POST запроса с валидными данными"""
        data = {
            'table_choice': str(self.table.id),
            'parameter_a': '1.5',
            'parameter_b': '2.5'
        }
        response = self.client.post(reverse('graph_view'), data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('graphic', response.context)
        self.assertIn('a', response.context)
        self.assertIn('b', response.context)
        self.assertIn('table_data', response.context)

        # Проверяем, что график - это base64 строка
        graphic = response.context['graphic']
        self.assertIsInstance(graphic, str)
        self.assertGreater(len(graphic), 100)

        # Проверяем параметры
        self.assertEqual(response.context['a'], 1.5)
        self.assertEqual(response.context['b'], 2.5)

    def test_graph_view_session_storage(self):
        """Тест сохранения графика в сессии"""
        data = {
            'table_choice': str(self.table.id),
            'parameter_a': '1.0',
            'parameter_b': '1.0'
        }
        response = self.client.post(reverse('graph_view'), data)

        # Проверяем сессию
        session = self.client.session
        self.assertIn('last_graph', session)
        self.assertIn('table_id', session)
        self.assertIn('param_a', session)
        self.assertIn('param_b', session)

    def test_graph_view_with_result(self):
        """Тест отображения графика с существующим результатом"""
        # Создаем результат расчета
        result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calc",
            param_a=1.5,
            param_b=2.5,
            table=self.table
        )

        # Сохраняем в сессии
        session = self.client.session
        session['result_id'] = result.id
        session.save()

        response = self.client.get(reverse('graph_view'))
        self.assertEqual(response.status_code, 200)

        # Проверяем, что форма предзаполнена
        form = response.context['form']
        self.assertEqual(float(form.initial['parameter_a']), 1.5)
        self.assertEqual(float(form.initial['parameter_b']), 2.5)

    def test_download_graph(self):
        """Тест скачивания графика"""
        # Сначала создаем график
        data = {
            'table_choice': str(self.table.id),
            'parameter_a': '1.0',
            'parameter_b': '1.0'
        }
        self.client.post(reverse('graph_view'), data)

        # Теперь скачиваем
        response = self.client.get(reverse('download_graph'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_download_graph_without_graph(self):
        """Тест скачивания без созданного графика"""
        response = self.client.get(reverse('download_graph'))

        # Должен быть редирект
        self.assertEqual(response.status_code, 302)


class ShareCalculationTest(TestCase):
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

        point = Point.objects.create(x_value=0.5, y_value=100.0)
        self.table.points.add(point)

        # Создаем результат расчета с данными
        table_data = [
            {'x2': 0.5, 'gexp': 100.0, 'gmod': 98.5, 'sigma': 1.5, 'delta': 1.5}
        ]

        self.result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calculation",
            param_a=1.5,
            param_b=2.5,
            table=self.table,
            iterations=100,
            exec_time=1.234,
            algorithm="Метод Гаусса",
            average_op=5.5,
            table_data=json.dumps(table_data)
        )

        self.client.login(username='testuser', password='testpass123')

    def test_share_calculation_get(self):
        """Тест GET запроса на страницу создания поста"""
        response = self.client.get(
            reverse('share_calculation', args=[self.result.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'forum_create.html')
        self.assertIn('form', response.context)
        self.assertIn('result', response.context)

    def test_share_calculation_post_valid(self):
        """Тест создания поста из расчета"""
        data = {
            'title': 'My Calculation Post',
            'content': 'Additional comments here'
        }
        response = self.client.post(
            reverse('share_calculation', args=[self.result.id]),
            data
        )

        # Проверяем редирект
        self.assertRedirects(response, reverse('forum_list'))

        # Проверяем, что пост создан
        post = Post.objects.get(calculation_result=self.result)
        self.assertEqual(post.title, 'My Calculation Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.source, 'calculation')

        # Проверяем snapshot
        self.assertIsNotNone(post.calculation_snapshot)
        self.assertEqual(post.calculation_snapshot['param_a'], 1.5)
        self.assertEqual(post.calculation_snapshot['param_b'], 2.5)

        # Проверяем технические поля
        self.assertEqual(post.algorithm, "Метод Гаусса")
        self.assertEqual(post.a12, "1.5")
        self.assertEqual(post.a21, "2.5")


class DeleteResultTest(TestCase):
    """Тесты для удаления результатов расчетов"""

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

        self.result = CalculationResult.objects.create(
            user=self.user,
            title="Test Calculation",
            param_a=1.5,
            param_b=2.5,
            table=self.table,
            table_data=json.dumps([{'x2': 0.5, 'gexp': 100}])
        )

        self.client.login(username='testuser', password='testpass123')

    def test_delete_own_result(self):
        """Тест удаления своего результата"""
        result_id = self.result.id

        response = self.client.post(
            reverse('delete_result', args=[result_id])
        )

        self.assertRedirects(response, reverse('profile'))

        # Проверяем, что результат удален
        self.assertFalse(
            CalculationResult.objects.filter(id=result_id).exists()
        )

    def test_delete_result_with_post(self):
        """Тест удаления результата со связанным постом"""
        # Создаем пост
        post = Post.objects.create(
            title="Test Post",
            content="Content",
            author=self.user,
            calculation_result=self.result,
            source='calculation'
        )

        response = self.client.post(
            reverse('delete_result', args=[self.result.id])
        )

        # Результат удален
        self.assertFalse(
            CalculationResult.objects.filter(id=self.result.id).exists()
        )

        # Пост остался
        post.refresh_from_db()
        self.assertIsNotNone(post.calculation_snapshot)

    def test_delete_other_user_result(self):
        """Тест попытки удаления чужого результата"""
        self.client.login(username='otheruser', password='testpass123')

        response = self.client.post(
            reverse('delete_result', args=[self.result.id])
        )

        self.assertRedirects(response, reverse('profile'))

        # Результат не удален
        self.assertTrue(
            CalculationResult.objects.filter(id=self.result.id).exists()
        )


class UpdateProfileExtendedTest(TestCase):
    """Расширенные тесты для обновления профиля"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_update_profile_username(self):
        """Тест изменения имени пользователя"""
        data = {
            'username': 'newusername',
            'email': 'test@example.com'
        }
        response = self.client.post(reverse('update_profile'), data)

        self.assertRedirects(response, reverse('profile'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_update_profile_duplicate_username(self):
        """Тест попытки использовать занятое имя"""
        User.objects.create_user(
            username='taken',
            password='pass'
        )

        data = {
            'username': 'taken',
            'email': 'test@example.com'
        }
        response = self.client.post(reverse('update_profile'), data)

        self.assertRedirects(response, reverse('profile'))

        # Имя не изменилось
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')

    def test_update_profile_email(self):
        """Тест изменения email"""
        data = {
            'username': 'testuser',
            'email': 'newemail@example.com'
        }
        response = self.client.post(reverse('update_profile'), data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')


class ForumIntegrationTest(TestCase):
    """Интеграционные тесты для форума"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_full_calculation_to_forum_workflow(self):
        """Тест полного цикла: расчет -> график -> пост на форуме"""
        # 1. Создаем таблицу
        table = Table.objects.create(
            title="Integration Test Table",
            temperature=298.15,
            author=self.user
        )

        for x in [0.2, 0.5, 0.8]:
            point = Point.objects.create(x_value=x, y_value=100 * x)
            table.points.add(point)

        # 2. Запускаем расчет
        calc_data = {
            'algorithm': 'gauss',
            'tabledata': '1'
        }
        calc_response = self.client.post(
            reverse('calculations'),
            calc_data
        )

        self.assertEqual(calc_response.status_code, 200)
        result_id = calc_response.json()['result_id']

        # 3. Создаем пост из расчета
        post_data = {
            'title': 'Integration Test Post',
            'content': 'Test content'
        }
        post_response = self.client.post(
            reverse('share_calculation', args=[result_id]),
            post_data
        )

        self.assertRedirects(post_response, reverse('forum_list'))

        # 4. Проверяем, что пост появился на форуме
        forum_response = self.client.get(reverse('forum_list'))
        self.assertContains(forum_response, 'Integration Test Post')

        # 5. Проверяем детали поста
        post = Post.objects.get(title='Integration Test Post')
        detail_response = self.client.get(
            reverse('forum_detail', args=[post.id])
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertIn('post', detail_response.context)
        self.assertIn('result_info', detail_response.context)