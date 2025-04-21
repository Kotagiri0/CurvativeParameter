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
