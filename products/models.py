from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )
    sub_category = models.ManyToManyField(
        'self',
        verbose_name='Подкатегория',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'Название',
        max_length=255,
        db_index=True
    )
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_index=True
    )
    category = models.ManyToManyField(
        Category,
        verbose_name='Категория',
        related_name='products',
        db_index=True
    )
    image = models.ImageField('Изображение')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.name} {self.category} {self.price}'
