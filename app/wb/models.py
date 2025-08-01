from django.db import models


class Product(models.Model):

    article = models.BigIntegerField(
        primary_key=True,
        verbose_name="Артикул Wildberries"
    )

    name = models.CharField(
        max_length=500,
        verbose_name="Название",
        blank=False
    )

    price = models.FloatField(
        verbose_name="Цена",
        blank=False
    )

    # Необязательные поля (могут отсутствовать в API)
    old_price = models.FloatField(
        verbose_name="Старая цена",
        null=True,
        blank=True
    )

    rating = models.FloatField(
        verbose_name="Рейтинг",
        null=True,
        blank=True
    )

    reviews = models.IntegerField(
        verbose_name="Количество отзывов",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.article} - {self.name}"
