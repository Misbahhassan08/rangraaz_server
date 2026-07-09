from django.urls import path


from .views import create_product, all_data, item_delete, item_update,create_category,create_subcategory,all_categories,all_subcategories,subcategories_by_category,delete_category,delete_subcategory,create_payment,link_category_subcategory,create_sub_subcategory,sub_subcategories_by_subcategory,link_subcategory_sub_subcategory,delete_sub_subcategory
from .views import update_slider,get_slider,manage_announcement,sale_products,total_products_count,get_product_by_sku,update_stock
from .views import page_list_create,page_detail_update_delete,page_by_slug,header_pages,header_group_list_create,header_group_detail,public_header_nav



urlpatterns = [
    
path('sub-subcategories/create/', create_sub_subcategory, name='create_sub_subcategory'),
path('sub-subcategories/by-subcategory/<int:subcategory_id>/', sub_subcategories_by_subcategory ,name='sub_subcategories_by_subcategory'),
path('sub-subcategories/link/', link_subcategory_sub_subcategory, name='link_subcategory_sub_subcategory'),
path('sub-subcategories/delete/<int:pk>/', delete_sub_subcategory,name='delete_sub_subcategory'),

    path('products/create/', create_product, name='create_product'),
    path('products/', all_data, name='all_products'),
    path('products/<int:pk>/delete/', item_delete, name='delete_product'),
    path('products/<int:pk>/update/', item_update, name='update_product'),
    
    path('categories/create/', create_category, name='create_category'),
    path('subcategories/create/', create_subcategory, name='create_subcategory'),
    path('categories/<int:pk>/delete/', delete_category, name='delete_category'),
    path('subcategories/<int:pk>/delete/', delete_subcategory, name='delete_subcategory'),
    
    path('categories/all/', all_categories, name='all_categories'),
    path('subcategories/all/', all_subcategories, name='all_subcategories'),
    path('subcategories/<int:category_id>/', subcategories_by_category),
       
    path("create-payment/", create_payment, name="create-payment"),
    path('update-slider/', update_slider, name='update-slider'),
    path('get-slider/',get_slider,name='get_slider'),
    path('manage_announcement/', manage_announcement, name='manage_announcement'),
    path('sale-items/', sale_products, name='sale_products'),
    path('link-category-subcategory/', link_category_subcategory, name='link_category_subcategory'),
    path('total-products/', total_products_count, name='total_products_count'), 
path('product-by-sku/<str:sku>/', get_product_by_sku, name='get_product_by_sku'),
path('update-stock/<int:pk>/', update_stock, name='update_stock'),
path('pages/', page_list_create, name='page_list_create'),
path('pages/<int:pk>/', page_detail_update_delete, name='page_detail_update_delete'),
path('pages/slug/<slug:slug>/', page_by_slug, name='page_by_slug'),
path('header-pages/', header_pages, name='header_pages'),
path('header-groups/', header_group_list_create, name='header_group_list_create'),
path('header-groups/<int:pk>/', header_group_detail, name='header_group_detail'),
path('header-nav/', public_header_nav, name='public_header_nav'),
]
