from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

#VERIFICATION EMAIL
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# TO ASSIGN CART ID TO THE LOGGED IN USER, so we can see list of crat items, selected before user is logged in, after user is logged in
from carts.views import get_cart_id
from carts.models import Cart, CartItem

import requests
from orders.models import Order, OrderProduct

from .utils import send_otp
from datetime import datetime
import pyotp

# Create your views here.
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name = first_name,
                last_name = last_name,
                username = username,
                email = email,
                password=password
            )
            user.phone = phone
            user.save()

            # create a dummy user profile while the registration process, so edit profile option is enabled, otherwise it will throw user profile 404 not found
            user_profile = UserProfile()
            user_profile.user = user
            user_profile.profile_pic = 'default/default_profile_pic.jpg'
            user_profile.save()

            # USER ACTIVATATION CODE
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()

            # messages.success(request, 'Thank you for registering in our site. We have sent you a verfiation mail to you registered email address, please activate your account!')
            # return redirect('register')
            return redirect('/accounts/login/?command=verification&email=' + email)
    else:
        form = RegistrationForm()
    
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(request, email=email, password=password)
        if user:

            # code to send otp
            request.session['email'] = email
            send_otp(request)
            return redirect('otp')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

def otp(request):
    
    if request.method == "POST":
        otp = request.POST['otp']
        email = request.session['email']

        otp_secret_key = request.session['otp_secret_key']
        otp_valid_until = request.session['otp_valid_until']

        if otp_secret_key and otp_valid_until is not None:
            valid_until = datetime.fromisoformat(otp_valid_until)

            if valid_until > datetime.now():
                totp = pyotp.TOTP(otp_secret_key, interval=60)

                print(totp.verify(otp))
                if totp.verify(otp):
                    user = get_object_or_404(Account, email=email)

                    # TO ASSIGN CART ID TO THE LOGGED IN USER, so we can see list of crat items, selected before user is logged in, after user is logged in
                    try:
                        cart = Cart.objects.get(cart_id=get_cart_id(request))
                        is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                        if is_cart_item_exists:
                            # GROUPING product variation before and after user logged in

                            #get product variation when user is not logged in (by using cart id)
                            product_variation_non_logged_in = []
                            cart_items = CartItem.objects.filter(cart=cart)
                            for cart_item in cart_items:
                                variation = cart_item.variation.all()
                                product_variation_non_logged_in.append(list(variation))
                            # print('-------------- non logged in--------')
                            # print(product_variation_non_logged_in) #[[<Variation: Blue>, <Variation: Small>]]

                            #get product variation when user is logged in (by using user)
                            product_variation_logged_in = []
                            cart_item_id_list = []
                            cart_items = CartItem.objects.filter(user=user)
                            for cart_item in cart_items:
                                variation = cart_item.variation.all()
                                product_variation_logged_in.append(list(variation))
                                cart_item_id_list.append(cart_item.id)
                            # print('---------logged in-----------')
                            # print(product_variation_logged_in) # [[<Variation: Black>, <Variation: Medium>], [<Variation: White>, <Variation: Medium>]]

                            # if product variation (when user is not logged in) present in product variation (when user is logged in),
                            # then increment cart item quantity by 1 and assign the user field of cart item model to the logged in user
                            # else assign the user field of cart item model to the logged in user
                            for product_variation in product_variation_non_logged_in:
                                if product_variation in product_variation_logged_in:
                                    index = product_variation_logged_in.index(product_variation)
                                    cart_item_id = cart_item_id_list[index]
                                    cart_item = CartItem.objects.get(id=cart_item_id)
                                    cart_item.quantity += 1
                                    cart_item.user = user
                                    cart_item.save()
                                else:
                                    cart_items_non_logged_in = CartItem.objects.filter(cart=cart)
                                    for cart_item in cart_items_non_logged_in:
                                        cart_item.user = user # assign the user field of cart item model to the logged in user
                                        cart_item.save()
                    except:
                        pass

                    auth.login(request, user)
                    messages.success(request, 'You are now logged in')

                    del request.session['otp_secret_key']
                    del request.session['otp_valid_until']

                    # CODE to handle if user hit cart checkout before LOGGED IN
                    url = request.META.get('HTTP_REFERER') # this will give the previous url
                    print(url) # http://127.0.0.1:8000/accounts/login/?next=/cart/checkout/
                    try:
                        query = requests.utils.urlparse(url).query
                        print(query) # next=/cart/checkout/
                        params = dict(x.split('=') for x in query.split('&'))
                        print(params) # {'next': '/cart/checkout/'}
                        if 'next' in params:
                            next_page = params['next']
                            return redirect(next_page)
                    except:
                        return redirect('dashboard')

                    return redirect('dashboard')
            
                else:
                    messages.error(request, 'Invalid OTP')
                    return redirect('otp')
            
            else:
                messages.error(request, 'OTP has expired')
                return redirect('otp')

        else:
            messages.error(request, 'OOPS, something went wrong!')
            return redirect('otp')

    return render(request, 'accounts/otp.html')

@login_required
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out!')
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulation! Your account is activated')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link!')
        user.delete()
        return redirect('register')

@login_required
def dashboard(request):

    if 'email' in request.session:
        del request.session['email']

    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()
    
    user_profile = UserProfile.objects.get(user=request.user)

    context = {
        'orders_count': orders_count,
        'user_profile': user_profile,
    }
    return render(request, 'accounts/dashboard.html', context)

def forgotPassword(request):
    if request.method == "POST":
        email = request.POST['email']
        try:
            user = Account.objects.get(email__exact=email)
        except Account.DoesNotExist:
            user = None
        
        if user:
            #FORGOT PASSWORD EMAIL CODE
            current_site = get_current_site(request)
            mail_subject = 'Please reset your password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()
            messages.success(request, 'Password reset email has been sent to your registered email address ' + email)
            return redirect('login')
        else:
            messages.error(request, 'Account doesnot exist')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def resetPassword_validation (request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password!')
        return redirect('resetPassword')
    else:
        messages.error(request, 'The reset password link has been expired!')
        return redirect('forgotPassword')

def resetPassword(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password has been reset successfully!')
            return redirect('login')
        else:
            messages.error(request, 'Password does not match')
            return redirect('resetPassword')
    return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at') # - will give in descending order
    context = {
        'orders': orders
    }
    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and user_profile_form.is_valid():
            user_form.save()
            user_profile_form.save()
            messages.success(request, 'Your profile has been updated')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        user_profile_form = UserProfileForm(instance=user_profile)

    context = {
        'user_form': user_form,
        'user_profile_form': user_profile_form,
        'user_profile': user_profile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(email__exact=request.user.email)
        if new_password == confirm_password:
            check_current_password = user.check_password(current_password) # to check if current password is correct or not
            # check_password() is an inbuilt method which will convert current password in hashed format and then check if the current password is correct or not and return True or False
            if check_current_password:
                user.set_password(new_password)
                user.save()
                # user can logged out from the system once password is reset
                # auth.logout(request)
                # django will automatically log you out
                messages.success(request, 'Your password is updated successfully!')
                return redirect('login')
            else:
                messages.error(request, 'Please enter correct current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match ')
            return redirect('change_password')
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'accounts/change_password.html', context)

@login_required(login_url='login')
def order_detail(request, order_number):
    order = Order.objects.get(order_number=order_number)
    order_detail = OrderProduct.objects.filter(order__order_number=order_number, is_ordered=True)
    # order is a foreign key in OrderProduct model, so we can use order_number of Order model by order__order_number inside OrderPorduct model
    # OR
    # order_detail = OrderProduct.objects.filter(order=order, is_ordered=True)
    context = {
        'order': order,
        'order_detail': order_detail,
    }
    return render(request, 'accounts/order_detail.html', context)