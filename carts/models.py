from django.db import models
from store.models import Product, Variation
from accounts.models import Account

# Create your models here.
class Cart(models.Model):
    cart_id = models.CharField(max_length=255, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    # this is to assign the cart id to the logged in user to reflect the cart items, selected when no user is logged in, once the user is logged in
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE) # a product can be part of different cart items, so when a product is deleted the associated cart items will get deleted
    
    variation = models.ManyToManyField(Variation, blank=True) # a product with many variations can be a part of different cart items
    '''
        many to many relation between CartItem and Variaton
        cart_item = CartItem.objects.get(id=34)
        cart_item.variation.all() # get all the objects of Variation Model (based on variation category) associated with the cart item
        here we have 2 variations for each cart item i.e. color and size
        [{item.variation_category: item.variation_value} for item in cart_item.variation.all()]   
        [{'color': 'White'}, {'size': 'Large'}]
    '''
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
    
    def sub_total(self):
        return self.product.price * self.quantity

    def __unicode__(self):
        return self.product
