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
    title = models.TextField(default="Untitled")
    solution = models.TextField(default="")
    points = models.ManyToManyField(Point, related_name="tables")
    temperature = models.FloatField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tables",
        verbose_name="Автор",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


class CalculationResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calculations")
    title = models.CharField(max_length=200, default="Без названия", verbose_name="Название расчета")
    param_a = models.FloatField()
    param_b = models.FloatField()

    # не каскадное удаление!
    table = models.ForeignKey(
        'Table',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="results"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    iterations = models.IntegerField(null=True, blank=True, verbose_name="Количество итераций")
    exec_time = models.FloatField(null=True, blank=True, verbose_name="Время выполнения (сек)")
    algorithm = models.CharField(max_length=100, null=True, blank=True, verbose_name="Алгоритм")
    average_op = models.FloatField(null=True, blank=True, verbose_name="Средняя относительная погрешность (%)")

    # сюда сохраняется копия данных таблицы
    table_data = models.TextField(null=True, blank=True, verbose_name="Данные таблицы")

    def get_table_data(self):
        """Возвращает JSON-данные таблицы (snapshot)."""
        if self.table_data:
            try:
                return json.loads(self.table_data)
            except json.JSONDecodeError:
                return self.table_data
        return None

    def __str__(self):
        return f"Calculation #{self.id} by {self.user.username}"



from cloudinary_storage.storage import MediaCloudinaryStorage

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        storage=MediaCloudinaryStorage(),
        upload_to='avatars/',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Profile of {self.user.username}"

from cloudinary_storage.storage import MediaCloudinaryStorage

from cloudinary_storage.storage import MediaCloudinaryStorage
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    SOURCE_CHOICES = [
        ('forum', 'Создан вручную на форуме'),
        ('calculation', 'Создан из расчёта'),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts", verbose_name="Автор")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")
    image = models.ImageField(
        storage=MediaCloudinaryStorage(),
        upload_to="post_images/",
        null=True,
        blank=True,
        verbose_name="Изображение"
    )

    calculation_result = models.ForeignKey(
        'CalculationResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Результат расчёта"
    )

    # 👇 Новое поле — snapshot (копия данных расчёта)
    calculation_snapshot = models.JSONField(null=True, blank=True, verbose_name="Копия данных расчета")

    algorithm = models.CharField(max_length=100, blank=True, null=True, verbose_name="Алгоритм")
    a12 = models.CharField(max_length=50, blank=True, null=True, verbose_name="A12")
    a21 = models.CharField(max_length=50, blank=True, null=True, verbose_name="A21")
    iterations = models.CharField(max_length=50, blank=True, null=True, verbose_name="Итерации")
    exec_time = models.CharField(max_length=50, blank=True, null=True, verbose_name="Время выполнения")
    average_error = models.CharField(max_length=50, blank=True, null=True, verbose_name="Средняя погрешность")

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='forum',
        verbose_name="Источник"
    )

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.title

    @property
    def is_from_calculation(self):
        """Проверка, создан ли пост из расчёта."""
        return self.source == 'calculation'

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор"
    )
    content = models.TextField("Комментарий", max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']

    def __str__(self):
        return f"Комментарий от {self.author.username} к '{self.post.title}'"