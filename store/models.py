from django.db import models
from category.models import Category
from django.urls import reverse

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=255, blank=True)
    price = models.IntegerField()
    image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    # When we delete a category, all the associated products will get deleteed automatically
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

# this will be used to separate variation category by color and size
class VariationManager(models.Manager):
    
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

variation_category_choices = (
    ('color', 'color'),
    ('size', 'size'),
)

# create variations of the product
class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE) # a product can have many variation
    variation_category = models.CharField(max_length=100, choices=variation_category_choices)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True) # disable any variation if you want
    created_date = models.DateTimeField(auto_now=True)
    
    # by this, you can access colors() and sizes() defined inside VariationManager using reverse many-to-one ralation
    '''
        p1 = Product.objects.get(id=1)
        p1.variation_set.all() # returns variation objects assiciated with product p1 object
        p1.variation_set.colors() # returns only variation objects filtered by variation category as color assiciated with product p1 object
        p1.variation_set.sizes() # returns only variation objects filtered by variation category as size assiciated with product p1 object 
    '''
    objects = VariationManager() 

    def __str__(self):
        return self.variation_value

# you can access product model fields by using variation object (foreign key many-to-one relation)
'''
    v1 = Variation.objects.get(id=1)
    v1.variation_value
    p11 = v1.product #product object
    p11.product_name

'''
# you can access variation model fields by using product object (reverse many-to-one relation)
'''
    p1 = Product.objects.get(id=1)
    v11 = p1.variation_set.all() # list of variation objects
    [variation_obj.product.product_name for variation_obj in v11 ]
    [variation_obj.variation_value for variation_obj in v11 ]
'''