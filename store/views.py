from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect

from .models import Product, ReviewRating
from category.models import Category

from carts.models import Cart, CartItem
from carts.views import get_cart_id

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

# Q is used to use OR operator in ORM complex queries
from django.db.models import Q

from .forms import ReviewForm
from django.contrib import messages

from orders.models import OrderProduct

# Create your views here.
def store(request, category_slug=None):
    
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug) #single object and it will throw error if you get multiple objects
        products = Product.objects.filter(category=categories, is_available=True) #queryset of list of objects
        products_count = products.count()
        # products = get_list_or_404(Product, category=categories, is_available=True) #list of objects
        # products_count = len(products)
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id') #fetch all products
        products_count = Product.objects.count()

    # use of paginator
    paginator = Paginator(products, 3) # number of products you want to see on a single page
    page = request.GET.get('page') # get page number from url query string /store?page=2
    products_per_page = paginator.get_page(page) # fetch only number of products defined above

    context = {
        'products': products_per_page,
        'products_count': products_count
    }
    return render(request, 'store/store.html', context)

# category__slug=category_slug is used to access slug field of category object (foreign key of Product Model)
def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)

        # check if a prodcut is already added to a cart or not
        if request.user.is_authenticated:
            is_product_in_cart = CartItem.objects.filter(user=request.user, product=single_product).exists()
        else:
            cart_id = get_cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            is_product_in_cart = CartItem.objects.filter(cart=cart, product=single_product).exists()
    except Exception as e:
        raise e
    
    # to check if the user has ordered the product or not from order product model
    if request.user.is_authenticated:
        try:
            order_product = OrderProduct.objects.filter(user=request.user, product__id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            order_product = None
    else:
        order_product = None

    # get all the reviews and list and show in the product detail page
    reviews = ReviewRating.objects.filter(product__id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'is_product_in_cart': is_product_in_cart,
        'order_product': order_product,
        'reviews': reviews,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET.get('keyword')
        if keyword:
            # filter the product objects if the keyword given in search option is found either in the product description or in the product name
            # __icontains is used to match the keyword and retruns objects if keyword is present
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            products_count = products.count()
        context = {
            'products': products,
            'products_count': products_count
        }
    return render(request, 'store/store.html', context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER') # store previous url
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id) 
            # double underscore is used to access the id field of user and product model as it is a foreignkey relationship with review model
            form = ReviewForm(request.POST, instance=reviews)
            # by passing instance, it will check if already a review is present or not and if present, then it will update the exisitng review
            # if we don't pass instance, then by default it will create a new form
            form.save()
            messages.success(request, 'Thank you! Your review has been updated')
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR') # store IP address
                data.product_id = product_id # OR data.product = product (product=Product.objects.get(id=product_id))
                data.user = request.user # OR data.user_id = request.user.id
                data.save()
                # above OR
                # subject = form.cleaned_data['subject']
                # rating = form.cleaned_data['rating']
                # ... get other fields
                # review = ReviewRating(
                #     subject=subject, rating=rating, .... other fields
                # )
                # review.save()
                messages.success(request, 'Thank you! Your review has been submitted')
        return redirect(url)