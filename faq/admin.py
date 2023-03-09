from django.contrib import admin

from faq.models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    pass
