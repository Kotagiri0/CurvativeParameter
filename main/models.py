from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Point(models.Model):
    x_value = models.FloatField()
    y_value = models.FloatField()

    def __str__(self):
        return f"{self.x_value}, {self.y_value}"

class Table(models.Model):
    title = models.TextField()
    solution = models.TextField()
    points = models.ManyToManyField(Point, related_name="points")
    temperature = models.FloatField()


class CalculationResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.TextField()
    algorithm = models.CharField(max_length=100)
    param_a = models.FloatField()
    param_b = models.FloatField()
    iterations = models.IntegerField()
    average_op = models.FloatField()
    exec_time = models.FloatField()
    table_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Результаты {self.algorithm} для {self.user.username}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
