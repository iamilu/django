from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from carts.models import CartItem
from .models import Order, Payment, OrderProduct
from .forms import OrderForm

from store.models import Product

import datetime
import json

from django.template.loader import render_to_string
from django.core.mail import EmailMessage

# Create your views here.
def place_order(request, total=0, qunatity=0, tax=0, grand_total=0):
    current_user = request.user
    if current_user.is_authenticated:
        # if card count is zero, then redirect to store
        cart_items = CartItem.objects.filter(user=request.user)
        cart_count = cart_items.count()
        if cart_count <= 0:
            return redirect('store')

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            qunatity += cart_item.quantity
        
        tax = 0.02 * total
        grand_total = total + tax

        if request.method == 'POST':
            form = OrderForm(request.POST)
            if form.is_valid():
                data = Order()
                data.user = request.user
                data.first_name = form.cleaned_data.get('first_name')
                data.last_name = form.cleaned_data.get('last_name')
                data.phone = form.cleaned_data.get('phone')
                data.email = form.cleaned_data.get('email')
                data.address_line_1 = form.cleaned_data.get('address_line_1')
                data.address_line_2= form.cleaned_data.get('address_line_2')
                data.country = form.cleaned_data.get('country')
                data.state = form.cleaned_data.get('state')
                data.city = form.cleaned_data.get('city')
                data.pincode = form.cleaned_data.get('pincode')
                data.order_note = form.cleaned_data.get('order_note')
                data.order_total = grand_total
                data.tax = tax
                data.ip = request.META.get('REMOTE_ADDR') # to get user ip address
                data.save()
                print(data)
                # generate order number
                current_date = str(datetime.date.today()).replace('-','')
                order_number = current_date + str(data.id)
                data.order_number = order_number
                data.save()

                # DISPLAY contact info, delivery info, product details, total, tax and grand total in payment page
                order = Order.objects.get(user=request.user, is_ordered=False, order_number=order_number)
                context = {
                    'order': order,
                    'cart_items': cart_items,
                    'total': total,
                    'tax': tax,
                    'grand_total': grand_total
                }
                
                return render(request, 'orders/payments.html', context)
            else:
                return redirect('checkout')
        else:
            try:
                order_queryset = Order.objects.filter(user=request.user, is_ordered=False)
                order = list(order_queryset)[-1]
                print(order) # get the latest order
                context = {
                        'order': order,
                        'cart_items': cart_items,
                        'total': total,
                        'tax': tax,
                        'grand_total': grand_total
                    }
                return render(request, 'orders/payments.html', context)
            except:
                return render(request, 'orders/payments.html')
    else:
        return redirect('login')

def payments(request):
    # get the request body from the frontend sent by the javascript fetch api
    body = json.loads(request.body)
    print(body)

    # store payment details in payment model
    payment = Payment(
        user = request.user,
        payment_id = body['payment_id'],
        payment_method = body['payment_method'],
        amount_paid = body['amount_paid'],
        status = body['status'],
    )
    payment.save()

    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['order_number'])
    order.payment = payment
    order.is_ordered = True
    order.save()

    # move cart items details to the order product table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order = order
        order_product.payment = payment
        order_product.user = request.user
        order_product.product = item.product
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.is_ordered = True
        order_product.save()

        # to assign value for many to many relation, you need to fist save the object
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variation.all() # get variation of each item
        order_product = OrderProduct.objects.get(id=order_product.id) # id will get generated as you have saved the object earlier
        order_product.variation.set(product_variation)
        order_product.save()

        # reduce the quantity of the sold products
        # product = models.ForeignKey(Product, on_delete=models.CASCADE) in CartItem model
        product = Product.objects.get(id=item.product_id) #you will get the associated product id for each cart item
        product.stock -= item.quantity
        product.save()

    # clear cart items
    CartItem.objects.filter(user=request.user).delete()

    # send order received email to the customer
    mail_subject = 'Thank you for your order ' + order.order_number
    message = render_to_string('orders/order_received_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_mail = EmailMessage(mail_subject, message, to=[to_email])
    send_mail.send()

    # send order number and payment details back to the sendData function present in java script via json response
    data = {
        'order_number': order.order_number,
        'payment_id': payment.payment_id,
        'status': payment.status,
    }

    # sending the json response of data back to the java script present in payments.html
    return JsonResponse(data)

def order_complete(request):
    # get order_number and payment_id from query string
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        payment = Payment.objects.get(payment_id=payment_id)
        order_product = OrderProduct.objects.filter(order=order, payment=payment)
        
        total = 0
        for item in order_product:
            total += item.product_price * item.quantity
        
        tax = total * 0.02
        grand_total = total + tax

        context = {
            'order': order,
            'payment': payment,
            'order_product': order_product,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
        }
    except (Order.DoesNotExist, Payment.DoesNotExist, OrderProduct.DoesNotExist):
        return redirect ('store')

    return render(request, 'orders/order_complete.html', context)