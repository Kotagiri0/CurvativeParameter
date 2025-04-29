import json

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Create your models here.
class Point(models.Model):
    x_value = models.FloatField()
    y_value = models.FloatField()

    def __str__(self):
        return f"{self.x_value}, {self.y_value}"

class Table(models.Model):
    title = models.TextField(default="Untitled")  # <-- Add default here
    solution = models.TextField(default="")
    points = models.ManyToManyField(Point, related_name="tables")
    temperature = models.FloatField()


class CalculationResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calculations")
    title = models.CharField(max_length=200, default="Без названия", verbose_name="Название расчета")
    param_a = models.FloatField()
    param_b = models.FloatField()
    table = models.ForeignKey('Table', on_delete=models.CASCADE, null=True, blank=True)  # Временно null=True
    created_at = models.DateTimeField(auto_now_add=True)
    iterations = models.IntegerField(null=True, blank=True, verbose_name="Количество итераций")
    exec_time = models.FloatField(null=True, blank=True, verbose_name="Время выполнения (сек)")
    algorithm = models.CharField(max_length=100, null=True, blank=True, verbose_name="Алгоритм")
    average_op = models.FloatField(null=True, blank=True, verbose_name="Средняя относительная погрешность (%)")
    table_data = models.TextField(null=True, blank=True, verbose_name="Данные таблицы")

    def get_table_data(self):
        if self.table_data:
            try:
                return json.loads(self.table_data)
            except json.JSONDecodeError:
                return self.table_data
        return None

    def __str__(self):
        return f"Calculation #{self.id} by {self.user.username}"

    class Meta:
        verbose_name = "Результат расчета"
        verbose_name_plural = "Результаты расчетов"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", verbose_name="Автор")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    image = models.ImageField(upload_to="post_images/", null=True, blank=True, verbose_name="Изображение")
    calculation_result = models.ForeignKey('CalculationResult', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.title
