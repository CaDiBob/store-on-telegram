from django.db import models


class Client(models.Model):
    tg_user_id = models.BigIntegerField(
        'Телеграм ID',
        unique=True,
        db_index=True
    )
    first_name = models.CharField('Имя', max_length=50)
    address = models.TextField('Адрес', blank=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f'{self.tg_user_id} {self.first_name}'
