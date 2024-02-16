# This will take request as an argument and return object as a dictionary just like context
# This context processors needs to be added in template scetion of settings.py 
# The categories can be used in any template as a variable

from .models import Category

def select_category(request):
    categories = Category.objects.all()
    return dict(categories=categories)