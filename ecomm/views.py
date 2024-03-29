from django.shortcuts import render

from store.models import Product, ReviewRating
from carts.models import Cart
from carts.views import get_cart_id

# Create your views here.
def index(request):

    # CREATE  CART ID/SESSION ID WHILE LOADING WEB SITE/INDEX PAGE to avoid session id missing error
    try:
        cart = Cart.objects.get(cart_id=get_cart_id(request)) #get the cart using cart_id/session id where items can be added
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = get_cart_id(request)
        )
    cart.save()

    products = Product.objects.all().filter(is_available=True).order_by('created_date')

    # get review rating
    for product in products:
        reviews = ReviewRating.objects.filter(product=product, status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'index.html', context)