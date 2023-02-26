from django.contrib import admin

from .models import Category, Product, Order, OrderItem


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


class OrederItemTubularInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('created_at',)

    inlines = (OrederItemTubularInline,)
