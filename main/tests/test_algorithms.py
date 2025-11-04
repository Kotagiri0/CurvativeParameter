"""
Тесты для алгоритмов оптимизации (gauss, gauss_step, gradient, gradient_step, otzhig)
"""
import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from main.models import Table, Point
from main import gauss, gauss_step, gradient, gradient_step, otzhig
import numpy as np


class AlgorithmTestCase(TestCase):
    """Базовый класс для тестов алгоритмов"""

    def setUp(self):
        """Создание тестового набора данных"""
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

        # Добавляем точки из тестового набора
        test_data = [
            (0.0697, 407),
            (0.0960, 523),
            (0.1038, 554),
            (0.1312, 634),
            (0.1325, 659),
            (0.2160, 888),
            (0.2739, 921),
            (0.4069, 1116),
            (0.4984, 1112),
            (0.5977, 1036),
            (0.6275, 994),
            (0.7020, 880),
            (0.7197, 846),
            (0.8078, 643),
            (0.8115, 634),
            (0.9187, 307),
        ]

        for x, y in test_data:
            point = Point.objects.create(x_value=x, y_value=y)
            self.table.points.add(point)

        # Создаем список таблиц для передачи в алгоритмы
        self.tables = [self.table]
        self.table_ind = 0

    def assertAlgorithmResults(self, result, algorithm_name):
        """Проверка общих свойств результатов алгоритма"""
        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Проверка типов
        self.assertIsInstance(a, float, f"{algorithm_name}: param_a должен быть float")
        self.assertIsInstance(b, float, f"{algorithm_name}: param_b должен быть float")
        self.assertIsInstance(iterations, int, f"{algorithm_name}: iterations должен быть int")
        self.assertIsInstance(exec_time, float, f"{algorithm_name}: exec_time должен быть float")

        # Проверка разумности параметров
        self.assertGreater(exec_time, 0, f"{algorithm_name}: время выполнения должно быть положительным")
        self.assertGreaterEqual(iterations, 0, f"{algorithm_name}: количество итераций должно быть >= 0")

        # Проверка длин списков (должны включать 0 и 1 на концах)
        expected_length = len(test_data) + 2  # +2 для x=0 и x=1
        self.assertEqual(len(l_x2), expected_length, f"{algorithm_name}: неверная длина l_x2")
        self.assertEqual(len(l_gmod), expected_length, f"{algorithm_name}: неверная длина l_gmod")
        self.assertEqual(len(l_gexp), expected_length, f"{algorithm_name}: неверная длина l_gexp")
        self.assertEqual(len(l_op), expected_length, f"{algorithm_name}: неверная длина l_op")
        self.assertEqual(len(l_ap), expected_length, f"{algorithm_name}: неверная длина l_ap")

        # Проверка граничных значений x
        self.assertAlmostEqual(l_x2[0], 0.0, places=2, msg=f"{algorithm_name}: первое значение x должно быть 0")
        self.assertAlmostEqual(l_x2[-1], 1.0, places=2, msg=f"{algorithm_name}: последнее значение x должно быть 1")

        # Проверка средней погрешности
        self.assertIsInstance(avg_op, float, f"{algorithm_name}: средняя погрешность должна быть float")
        self.assertGreaterEqual(avg_op, 0, f"{algorithm_name}: средняя погрешность должна быть >= 0")

        print(f"\n{algorithm_name} результаты:")
        print(f"  a={a:.3f}, b={b:.3f}")
        print(f"  Итераций: {iterations}")
        print(f"  Время: {exec_time:.3f} сек")
        print(f"  Средняя погрешность: {avg_op:.1f}%")


class GaussAlgorithmTest(AlgorithmTestCase):
    """Тесты для алгоритма Гаусса"""

    def test_gauss_basic(self):
        """Базовый тест метода Гаусса"""
        result = gauss.gauss(self.tables, self.table_ind)
        self.assertAlgorithmResults(result, "Метод Гаусса")

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Проверка, что алгоритм сошелся
        self.assertLess(avg_op, 50, "Средняя погрешность слишком велика")

    def test_gauss_with_custom_params(self):
        """Тест метода Гаусса с настраиваемыми параметрами"""
        result = gauss.gauss(
            self.tables,
            self.table_ind,
            eps=1e-6,
            max_iters=1000,
            init_step=0.1
        )
        self.assertAlgorithmResults(result, "Метод Гаусса (custom)")

    def test_gauss_empty_table(self):
        """Тест метода Гаусса с пустой таблицей"""
        empty_table = Table.objects.create(
            title="Empty Table",
            temperature=298.15,
            author=self.user
        )
        result = gauss.gauss([empty_table], 0)

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result
        self.assertEqual(a, 0.0)
        self.assertEqual(b, 0.0)
        self.assertEqual(iterations, 0)


class GaussStepAlgorithmTest(AlgorithmTestCase):
    """Тесты для метода Гаусса с переменным шагом"""

    def test_gauss_step_basic(self):
        """Базовый тест метода Гаусса с переменным шагом"""
        result = gauss_step.gauss_step(self.tables, self.table_ind)
        self.assertAlgorithmResults(result, "Метод Гаусса с переменным шагом")

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Проверка сходимости
        self.assertLess(avg_op, 50, "Средняя погрешность слишком велика")

    def test_gauss_step_convergence(self):
        """Тест сходимости метода Гаусса с переменным шагом"""
        result = gauss_step.gauss_step(
            self.tables,
            self.table_ind,
            eps=1e-8,
            max_iters=10000
        )
        self.assertAlgorithmResults(result, "Метод Гаусса с переменным шагом (convergence)")

    def test_gauss_step_empty_table(self):
        """Тест с пустой таблицей"""
        empty_table = Table.objects.create(
            title="Empty Table",
            temperature=298.15,
            author=self.user
        )
        result = gauss_step.gauss_step([empty_table], 0)

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result
        self.assertEqual(a, 0.0)
        self.assertEqual(b, 0.0)


class GradientAlgorithmTest(AlgorithmTestCase):
    """Тесты для метода градиентного спуска"""

    def test_gradient_basic(self):
        """Базовый тест градиентного спуска"""
        result = gradient.gradient(self.tables, self.table_ind)
        self.assertAlgorithmResults(result, "Метод градиентного спуска")

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Проверка сходимости
        self.assertLess(avg_op, 50, "Средняя погрешность слишком велика")

    def test_gradient_with_initial_params(self):
        """Тест градиентного спуска с начальными параметрами"""
        result = gradient.gradient(
            self.tables,
            self.table_ind,
            initial_params=(5.0, 5.0),
            eps=1e-6,
            max_iters=5000
        )
        self.assertAlgorithmResults(result, "Градиентный спуск (с начальными параметрами)")

    def test_gradient_empty_table(self):
        """Тест с пустой таблицей"""
        empty_table = Table.objects.create(
            title="Empty Table",
            temperature=298.15,
            author=self.user
        )
        result = gradient.gradient([empty_table], 0)

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result
        self.assertEqual(a, 0.0)
        self.assertEqual(b, 0.0)


class GradientStepAlgorithmTest(AlgorithmTestCase):
    """Тесты для метода градиентного спуска с переменным шагом"""

    def test_gradient_step_basic(self):
        """Базовый тест градиентного спуска с переменным шагом"""
        result = gradient_step.gradient_step(self.tables, self.table_ind)
        self.assertAlgorithmResults(result, "Градиентный спуск с переменным шагом")

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Проверка сходимости
        self.assertLess(avg_op, 50, "Средняя погрешность слишком велика")

    def test_gradient_step_convergence(self):
        """Тест сходимости с жесткими параметрами"""
        result = gradient_step.gradient_step(
            self.tables,
            self.table_ind,
            eps=1e-6,
            max_iters=10000
        )
        self.assertAlgorithmResults(result, "Градиентный спуск (convergence)")

    def test_gradient_step_empty_table(self):
        """Тест с пустой таблицей"""
        empty_table = Table.objects.create(
            title="Empty Table",
            temperature=298.15,
            author=self.user
        )
        result = gradient_step.gradient_step([empty_table], 0)

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result
        self.assertEqual(a, 0.0)
        self.assertEqual(b, 0.0)


class OtzhigAlgorithmTest(AlgorithmTestCase):
    """Тесты для метода симуляции отжига"""

    def test_otzhig_basic(self):
        """Базовый тест метода симуляции отжига"""
        result = otzhig.otzhig(self.tables, self.table_ind)
        self.assertAlgorithmResults(result, "Метод симуляции отжига")

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result

        # Симуляция отжига может давать разные результаты
        # Проверяем только разумность
        self.assertLess(avg_op, 100, "Средняя погрешность чрезмерно велика")

    def test_otzhig_with_params(self):
        """Тест метода симуляции отжига с параметрами"""
        result = otzhig.otzhig(
            self.tables,
            self.table_ind,
            init_temp=10.0,
            cooling=0.99,
            eps=1e-6,
            max_iters=10000
        )
        self.assertAlgorithmResults(result, "Симуляция отжига (custom)")

    def test_otzhig_empty_table(self):
        """Тест с пустой таблицей"""
        empty_table = Table.objects.create(
            title="Empty Table",
            temperature=298.15,
            author=self.user
        )
        result = otzhig.otzhig([empty_table], 0)

        a, b, iterations, exec_time, l_x2, l_gmod, l_gexp, l_op, l_ap, avg_op = result
        self.assertEqual(a, 0.0)
        self.assertEqual(b, 0.0)


class AlgorithmComparisonTest(AlgorithmTestCase):
    """Сравнительные тесты алгоритмов"""

    def test_all_algorithms_converge(self):
        """Тест, что все алгоритмы сходятся на одних данных"""
        results = {}

        # Запускаем все алгоритмы
        results['gauss'] = gauss.gauss(self.tables, self.table_ind)
        results['gauss_step'] = gauss_step.gauss_step(self.tables, self.table_ind)
        results['gradient'] = gradient.gradient(self.tables, self.table_ind)
        results['gradient_step'] = gradient_step.gradient_step(self.tables, self.table_ind)
        results['otzhig'] = otzhig.otzhig(self.tables, self.table_ind, max_iters=5000)

        print("\n" + "=" * 60)
        print("СРАВНЕНИЕ АЛГОРИТМОВ")
        print("=" * 60)

        for name, result in results.items():
            a, b, iterations, exec_time, _, _, _, _, _, avg_op = result
            print(f"\n{name.upper()}:")
            print(f"  Параметры: a={a:.3f}, b={b:.3f}")
            print(f"  Итераций: {iterations}")
            print(f"  Время: {exec_time:.3f} сек")
            print(f"  Погрешность: {avg_op:.1f}%")

            # Все должны дать разумные результаты
            self.assertLess(avg_op, 100, f"{name}: погрешность слишком велика")

    def test_algorithm_performance(self):
        """Тест производительности алгоритмов"""
        import time

        algorithms = [
            ('Gauss', lambda: gauss.gauss(self.tables, self.table_ind, max_iters=1000)),
            ('Gauss Step', lambda: gauss_step.gauss_step(self.tables, self.table_ind, max_iters=1000)),
            ('Gradient', lambda: gradient.gradient(self.tables, self.table_ind, max_iters=1000)),
            ('Gradient Step', lambda: gradient_step.gradient_step(self.tables, self.table_ind, max_iters=1000)),
            ('Otzhig', lambda: otzhig.otzhig(self.tables, self.table_ind, max_iters=1000)),
        ]

        print("\n" + "=" * 60)
        print("ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("=" * 60)

        for name, algo_func in algorithms:
            start = time.time()
            result = algo_func()
            elapsed = time.time() - start

            _, _, iterations, exec_time, _, _, _, _, _, avg_op = result

            print(f"\n{name}:")
            print(f"  Внешнее время: {elapsed:.3f} сек")
            print(f"  Внутреннее время: {exec_time:.3f} сек")
            print(f"  Итераций: {iterations}")
            print(f"  Погрешность: {avg_op:.1f}%")


class HelperFunctionsTest(TestCase):
    """Тесты вспомогательных функций"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test')
        self.table = Table.objects.create(
            title="Test",
            temperature=298.15,
            author=self.user
        )
        point = Point.objects.create(x_value=0.5, y_value=100.0)
        self.table.points.add(point)

    def test_func_gauss(self):
        """Тест функции модели из gauss"""
        result = gauss.func(1.0, 1.0, 0.5, [self.table], 0)
        self.assertIsInstance(result, (float, np.ndarray))

    def test_sum_of_deviations_gauss(self):
        """Тест функции отклонений из gauss"""
        l_points = [(0.5, 100.0)]
        result = gauss.sum_of_deviations(1.0, 1.0, [self.table], 0, l_points)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0)

    def test_func_gradient(self):
        """Тест функции модели из gradient"""
        result = gradient.func([1.0, 1.0], 0.5, 298.15)
        self.assertIsInstance(result, (float, np.ndarray))

    def test_derivative_gradient(self):
        """Тест функции производной из gradient"""
        x2_arr = np.array([0.5])
        gexp_arr = np.array([100.0])
        result = gradient.derivative([1.0, 1.0], x2_arr, gexp_arr, 298.15)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)


# Добавляем маркер для медленных тестов
test_data = [
    (0.0697, 407), (0.0960, 523), (0.1038, 554), (0.1312, 634),
    (0.1325, 659), (0.2160, 888), (0.2739, 921), (0.4069, 1116),
    (0.4984, 1112), (0.5977, 1036), (0.6275, 994), (0.7020, 880),
    (0.7197, 846), (0.8078, 643), (0.8115, 634), (0.9187, 307),
]