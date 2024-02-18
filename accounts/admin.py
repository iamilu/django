from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, UserProfile

from django.utils.html import format_html

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

class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;">'.format(object.profile_pic.url))
    thumbnail.short_description = 'Profile Picture' # title of the thumbnail to be shown in the admin page table
    
    def full_name(self, object):
        return object.user.first_name.capitalize() + ' ' + object.user.last_name.capitalize()
    full_name.short_description = 'Name'

    def email(self, object):
        return object.user.email
    email.short_description = 'Email Address'

    def phone(self, object):
        return object.user.phone
    phone.short_description = 'Phone Number'

    list_display = ['thumbnail', 'full_name', 'user', 'phone', 'city', 'pincode', 'state', 'country']

admin.site.register(Account, AccountAdmin)
admin.site.register(UserProfile, UserProfileAdmin)