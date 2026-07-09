from django.urls import path
from .views import OrderCreateView,get_all_orders,get_order_by_id,OrderStatusUpdateView,update_order_shipment,delete_order


urlpatterns = [
        path("orders/create/", OrderCreateView.as_view(), name="order-create"),
        path('all-orders/', get_all_orders, name='all_orders'),
        path("orders/<int:pk>/", get_order_by_id, name="get_order_by_id"),
        path("orders/<int:order_id>/update_status/", OrderStatusUpdateView.as_view(), name="order_status_update"),
        path('orders/<int:order_id>/update-shipment/', update_order_shipment),
        path('orders/delete/<int:order_id>/', delete_order, name='delete_order')

    
]
