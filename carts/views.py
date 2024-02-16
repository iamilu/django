from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem

from django.core.exceptions import ObjectDoesNotExist

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.
def get_cart_id(request): #cart_id is nothing but the session id which we can use to add items in a cart
    cart_id = request.session.session_key #get the session id
    if not cart_id:
        cart_id = request.session.create() #create new session id if not present
    return cart_id

def add_cart(request, product_id):
    # http://127.0.0.1:8000/cart/add_cart/2/?color=blue&size=small
    # name parameter used in select tag of product_detail.html
    product = Product.objects.get(id=product_id) #get the product (item) which will be added to the cart

    # code to get list of products with variations also add it to the CartItems Model
    # product variation --> blue medium, green large etc
    product_variation = []
    if request.method == 'POST':
        for key in request.POST:
            value = request.POST.get(key)
            print(key, value) #color blue, size small
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value) # __iexact will ignore case sensitive
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass
    print(product_variation) #[<Variation: Blue>, <Variation: Small>]
    
    # if user is logged in, then use user object for cart items operations
    if request.user.is_authenticated:
        # get the list of existing cart items
        cart_items = CartItem.objects.filter(product=product, user=request.user)

        # if cart item exists, get the list of product variation
        if cart_items.exists():
            existing_variation_list = []
            existing_cart_item_id_list = []
            for cart_item in cart_items:
                existing_variation = cart_item.variation.all()
                existing_variation_list.append(list(existing_variation))
                existing_cart_item_id_list.append(cart_item.id)

            # if current product variation present, then increment the cart item by 1
            if product_variation in existing_variation_list:
                existing_variation_index = existing_variation_list.index(product_variation)
                existing_cart_item_id = existing_cart_item_id_list[existing_variation_index]
                cart_item = CartItem.objects.get(id=existing_cart_item_id)
                cart_item.quantity += 1
                cart_item.save()
            
            # if current product variation is not present, then add new cart item
            else:
                cart_item = CartItem.objects.create(
                    product=product,
                    user=request.user,
                    quantity=1
                )
                if len(product_variation) > 0:
                    cart_item.variation.clear()
                    cart_item.variation.add(*product_variation)
                cart_item.save()

        # if caart item is not present, then add new cart item
        else:
            cart_item = CartItem.objects.create(
                product=product,
                user=request.user,
                quantity=1
            )
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()
    
    # if user is not logged in then use cart id for cart items operations
    else:

        try:
            cart = Cart.objects.get(cart_id=get_cart_id(request)) #get the cart using cart_id/session id where items can be added
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = get_cart_id(request)
            )   
        cart.save()

        # we have prodcut and cart, so now need to add product/item inside the cart
        # in one cart we can have multiple products (which is nothing but cart items)
        cart_items = CartItem.objects.filter(product=product, cart=cart)

        # check if any cart item exists
        # if exists, then get the varient objects for each cart item and add it to a list
        # exisiting variation list
        if cart_items.exists():
            existing_variation_list = [] #product variation list
            existing_cart_item_id_list = []
            for cart_item in cart_items:
                existing_variation = cart_item.variation.all()
                existing_variation_list.append(list(existing_variation))
                existing_cart_item_id_list.append(cart_item.id)

            # check if the current variation (product_variation) is present in existing variation list
            # if exists, then increase the cart item by 1
            # if not exists, then create a new cart item
            if product_variation in existing_variation_list:
                existing_variation_index = existing_variation_list.index(product_variation)
                existing_cart_item_id = existing_cart_item_id_list[existing_variation_index]
                cart_item = CartItem.objects.get(id=existing_cart_item_id)
                cart_item.quantity += 1
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    product = product,
                    cart = cart,
                    quantity = 1
                )
                if len(product_variation) > 0:
                    cart_item.variation.clear()
                    cart_item.variation.add(*product_variation)
                cart_item.save()

        else:
            cart_item = CartItem.objects.create(
                product = product,
                cart = cart,
                quantity = 1
            )
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()

    return redirect('cart')

# decrement the qunatity by 1
def remove_cart(request, product_id, cart_item_id):
    # product = get_object_or_404(Product, id=product_id)
    product = Product.objects.get(id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=get_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

# remove entire item from the cart when click on remove
def remove_cart_item(request, product_id, cart_item_id):
    product = Product.objects.get(id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=get_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def cart(request, total=0, qunatity=0, cart_items=None, tax=0, grand_total=0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=get_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
    except ObjectDoesNotExist:
        pass

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        qunatity += cart_item.quantity

    tax = 0.02 * total
    grand_total = total + tax
    context = {
        'total': total,
        'qunatity': qunatity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, qunatity=0, cart_items=None, tax=0, grand_total=0):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=get_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
    except ObjectDoesNotExist:
        pass

    for cart_item in cart_items:
        total += cart_item.product.price * cart_item.quantity
        qunatity += cart_item.quantity

    tax = 0.02 * total
    grand_total = total + tax
    context = {
        'total': total,
        'qunatity': qunatity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/checkout.html', context)