from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .models import Account
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
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request, 'accounts/login.html')

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
    return render(request, 'accounts/dashboard.html')

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