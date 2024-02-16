from .models import Cart, CartItem
from carts.views import get_cart_id

def carts_count(request):
    total_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=get_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.filter(cart=cart[:1])
            for cart_item in cart_items:
                total_count += cart_item.quantity
        except Cart.DoesNotExist:
            total_count = 0
        return dict(total_count=total_count)