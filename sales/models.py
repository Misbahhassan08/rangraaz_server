from django.db import models
from rangraaz.models import Customer

\

class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Credit/Debit Card'),
        ('PAYPAL', 'PayPal'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,  #  was CASCADE — guest has no user so can't cascade
        null=True,                   #  allows guest orders (no user)
        blank=True,
        related_name="orders"
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipment_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)

    shipping_address = models.JSONField(
        default=dict,
        help_text="Store shipping details as JSON object with keys: email, first_name, last_name, address, city, zipcode, state"
    )

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    products = models.JSONField(default=list)

    def __str__(self):
        # safe for guests who have no user
        return f"Order #{self.order_id} by {self.user.username if self.user else 'Guest'}"