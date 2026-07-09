from django.db import models
from cloudinary.models import CloudinaryField
from django.core.validators import MinLengthValidator

class Products(models.Model):
    product_name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=100)
    
    # --- Sale Fields ---
    original_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in USD")
    discount_percentage = models.PositiveIntegerField(default=0)
    is_sale_on = models.BooleanField(default=False)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    quantity = models.PositiveIntegerField()
    
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products'
    )
    subcategory = models.ForeignKey(
        'SubCategory', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products'
    )
    sub_subcategory = models.ForeignKey(
    'SubSubCategory',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='products'
    )
    
    size = models.CharField(max_length=50, blank=True, null=True)
    vendor = models.CharField(max_length=255)
    sku = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(5, message="SKU must be at least 5 characters long.")]
    )

    def save(self, *args, **kwargs):
        orig_price = float(self.original_price or 0)
        discount = float(self.discount_percentage or 0)

        if self.is_sale_on and discount > 0:
            discount_amount = (orig_price * discount) / 100
            self.sell_price = round(orig_price - discount_amount, 2)
        else:
            self.sell_price = orig_price
        
        super(Products, self).save(*args, **kwargs)
        
        
        
  

class ProductImage(models.Model):
    product = models.ForeignKey(
        Products, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = CloudinaryField('image')
    label = models.CharField(max_length=50, blank=True, null=True)  # front, back etc
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.product_name} - image {self.order}"
             
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    


class CategorySubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_subcategories')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='subcategory_categories')

    class Meta:
        unique_together = ('category', 'subcategory')  

    def __str__(self):
        return f"{self.category.name} - {self.subcategory.name}"
    
    
class SubSubCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class SubCategorySubSubCategory(models.Model):
    subcategory = models.ForeignKey(
        SubCategory, 
        on_delete=models.CASCADE, 
        related_name='sub_subcategories'
    )
    sub_subcategory = models.ForeignKey(
        SubSubCategory, 
        on_delete=models.CASCADE, 
        related_name='subcategories'
    )

    class Meta:
        unique_together = ('subcategory', 'sub_subcategory')

    def __str__(self):
        return f"{self.subcategory.name} → {self.sub_subcategory.name}"
    
    
    
    
    
    
    
    
 # ..................slider.........

class Slider(models.Model):
    slide_index = models.IntegerField(unique=True) 
    image = CloudinaryField('image') 
    link = models.CharField(max_length=500, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Slide {self.slide_index}"

class SiteSettings(models.Model):
    announcement_text = models.CharField(max_length=255)
    is_scrolling = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.announcement_text
    
    
class SizeStock(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name='size_stocks'
    )
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.product_name} - {self.size}: {self.quantity}"


class CustomPage(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    meta_description = models.TextField(blank=True, null=True)
    show_in_header = models.BooleanField(default=False)
    nav_label = models.CharField(max_length=80, blank=True, null=True)
    nav_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='nav_children'
    )
    nav_image = CloudinaryField('image', blank=True, null=True)
    header_group = models.ForeignKey(
        'HeaderGroup',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pages'
    )
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title


class PageBlock(models.Model):
    BLOCK_CHOICES = [
        ('slider', 'Slider'),
        ('campaign', 'Campaign'),
        ('products', 'Products'),
    ]

    page = models.ForeignKey(CustomPage, on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=30, choices=BLOCK_CHOICES)
    title = models.CharField(max_length=180, blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    height = models.PositiveIntegerField(default=520)
    image = CloudinaryField('image', blank=True, null=True)
    video = CloudinaryField('video', resource_type='video', blank=True, null=True)
    link = models.CharField(max_length=500, blank=True, null=True)
    product_ids = models.JSONField(default=list, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.page.title} - {self.block_type}"


class HeaderGroup(models.Model):
    STYLE_CHOICES = [
        ('standard', 'Standard'),
        ('sale', 'Sale'),
        ('featured', 'Featured'),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    direct_url = models.CharField(max_length=500, blank=True, null=True)
    hover_title = models.CharField(max_length=120, blank=True, null=True)
    hover_subtitle = models.CharField(max_length=255, blank=True, null=True)
    hover_image = CloudinaryField('image', blank=True, null=True)
    button_style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='standard')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_dropdown = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'title']

    def __str__(self):
        return self.title
