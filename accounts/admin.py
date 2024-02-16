from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

# Register your models here.

# This will display the mentioned fields in the admin panel for Account table
class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined','is_active')
    list_display_links = ('email', 'first_name', 'last_name') #enable link to see the details in admin panel
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',) # In descending order

    filter_horizontal = ()
    list_filter = ()
    fieldsets = () # This will make password readonly

admin.site.register(Account, AccountAdmin)