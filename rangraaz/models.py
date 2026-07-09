from django.db import models
class Customer(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]
    name = models.CharField(max_length=100) 
    password = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, null=True, blank=True) 
    address = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    email = models.EmailField(null=True, blank=True)       
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True) 

    def __str__(self):
        return f"{self.name} ({self.role})"