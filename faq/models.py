from django.db import models

class FAQ(models.Model):
    question = models.TextField('Вопрос')
    answer = models.TextField('Ответ')

    class Meta:
        verbose_name = 'Часто задаваемый вопрос'
        verbose_name_plural = 'Часто задаваемые вопросы'

    def __str__(self):
        return f'{self.question}'
