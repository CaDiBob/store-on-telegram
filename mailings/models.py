from django.db import models


class Mailing(models.Model):
    text = models.TextField('Текст')
    start_date = models.DateTimeField('Начало рассылики', blank=True)
    is_finish = models.BooleanField('Завершена', default=False)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'

    def __str__(self):
        return f'{self.start_date.strftime("%m-%d-%Y %H:%M")}'
