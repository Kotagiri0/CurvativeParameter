from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class Point(models.Model):
    x_value = models.FloatField()
    y_value = models.FloatField()

    def __str__(self):
        return f"{self.x_value}, {self.y_value}"


class Table(models.Model):
    title = models.TextField(default="Untitled")
    solution = models.TextField(default="")
    points = models.ManyToManyField(Point, related_name="tables")
    temperature = models.FloatField(default=0.0)  # Добавлен default


class CalculationResult(models.Model):
    ALGORITHM_CHOICES = [
        ('unknown', 'Неизвестный алгоритм'),
        ('annealing', 'Имитация отжига'),
        ('genetic', 'Генетический алгоритм'),
        ('gradient', 'Градиентный спуск'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calculation_results',
        verbose_name='Пользователь'
    )

    title = models.CharField(
        max_length=200,
        default='Новый расчет',
        verbose_name='Название расчета'
    )

    algorithm = models.CharField(
        max_length=100,
        choices=ALGORITHM_CHOICES,
        default='unknown',
        verbose_name='Алгоритм'
    )

    param_a = models.FloatField(
        verbose_name='Параметр А',
        default=0.0  # Добавлено
    )

    param_b = models.FloatField(
        verbose_name='Параметр Б',
        default=0.0  # Добавлено
    )

    iterations = models.PositiveIntegerField(
        verbose_name='Итерации',
        default=1  # Добавлено
    )

    average_op = models.FloatField(
        default=0.0,
        verbose_name='Среднее значение'
    )

    exec_time = models.FloatField(
        default=0.0,
        verbose_name='Время выполнения (сек)'
    )

    table_data = models.JSONField(
        default=dict,
        verbose_name='Таблица данных'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Результат расчета'
        verbose_name_plural = 'Результаты расчетов'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['algorithm']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Результаты {self.get_algorithm_display()} для {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.title.strip():
            self.title = f"Расчет {self.algorithm} от {self.created_at.strftime('%Y-%m-%d')}"
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
