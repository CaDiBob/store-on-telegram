from django.contrib import admin

from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    raw_id_fields = ('sub_category',)

    list_display = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    raw_id_fields = ('category',)

    list_display = (
        'name',
        'description',
        'image',
        'price'
    )
