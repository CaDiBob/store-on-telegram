from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

from clients.models import Client


class Category(models.Model):
    name = models.CharField(
        'Название',
        max_length=50
    )
    sub_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        verbose_name='Категория',
        related_name='categories',
        blank=True,
        null=True,
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
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        related_name='products',
        null=True,
        db_index=True
    )
    image = models.ImageField(
        'Изображение',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.name} {self.category} {self.price}'


class Order(models.Model):
    client = models.ForeignKey(
        Client,
        verbose_name='Клиент',
        on_delete=models.CASCADE,
        related_name='orders',
    )
    created_at = models.DateTimeField(
        'Когда создан',
        default=timezone.now,
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.client.tg_user_id} {self.created_at}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        related_name='order_items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        related_name='items',
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Пункт заказа'
        verbose_name_plural = 'Пункты заказа'

    def __str__(self):
        return f'{self.product.name} {self.quantity}'
