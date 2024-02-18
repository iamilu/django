from django.contrib import admin
from .models import Product, Variation, ReviewRating, productGallery

import admin_thumbnails
# admin thumbnail is used to preview the image field in admin page for product Gallery

# Register your models here.
@admin_thumbnails.thumbnail('image')
class productGalleryInline(admin.TabularInline):
    model = productGallery
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {
        'slug': ('product_name',)
    }
    inlines = [productGalleryInline]

class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category', 'variation_value')

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(productGallery)