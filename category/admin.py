from django.contrib import admin
from .models import Category

# Register your models here.

# This will auto populat the slug field when we enter value in category_name field
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('category_name',)
    }
    # this will deiplay the fields in front page of the admin panel
    list_display = ('category_name', 'slug')

admin.site.register(Category, CategoryAdmin)