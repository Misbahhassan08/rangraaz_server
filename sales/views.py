import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import requests
from .models import Order, Customer
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.http import JsonResponse
from collections import Counter
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.timezone import now





from django.core.mail import send_mail
from django.conf import settings


@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            user_id = data.get("user")
            user = None
            if user_id:
                try:
                    user = Customer.objects.get(id=user_id)
                except Customer.DoesNotExist:
                    return JsonResponse({"success": False, "error": "User not found"}, status=400)

            # Create order
            order = Order.objects.create(
                user=user,
                total_price=data.get("total_price"),
                shipment_id=data.get("shipment_id"),
                tracking_id=data.get("tracking_id"),
                shipping_address=data.get("shipping_address"),
                payment_method=data.get("payment_method"),
                status=data.get("status", "PENDING"),
                products=data.get("products", [])
            )

            # --- EMAIL LOGIC START ---
            shipping_info = data.get("shipping_address", {})
            user_email = shipping_info.get("email")
            user_name = shipping_info.get("name", getattr(user, "name", "Customer") if user else "Customer")

            if user_email:
                subject = f"Order Confirmed - Rang Raaz (#{order.order_id})"

                context = {
                    'user_name': user_name if user_name else "Customer",
                    'order_id': order.order_id,
                    'date': now().strftime('%B %d, %Y'),
                    'items': [
                        {
                            'name': item.get('name'),
                            'quantity': item.get('quantity'),
                            'price': item.get('price'),
                            'image': item.get('image', '')
                        }
                        for item in order.products
                    ] if isinstance(order.products, list) else [],
                    'total_amount': order.total_price,
                    'payment_method': "Cash on Delivery" if order.payment_method == "COD" else order.payment_method,
                    'billing_address': {
                        'name': user_name,
                        'street': shipping_info.get("street", "N/A"),
                        'city': shipping_info.get("city", "N/A"),
                        'phone': shipping_info.get("phone", "N/A")
                    }
                }

                html_message = render_to_string('order_email.html', context)
                plain_message = strip_tags(html_message)

                try:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_message,
                        from_email=settings.EMAIL_HOST_USER,
                        to=[user_email],
                    )
                    email.attach_alternative(html_message, "text/html")
                    email.send()
                    print(f"✅ Professional HTML email sent to {user_email}")
                except Exception as mail_err:
                    print(f"❌ Mail error: {str(mail_err)}")
            # --- EMAIL LOGIC END ---

            return JsonResponse({
                "success": True,
                "message": "Order created successfully",
                "order_id": order.order_id,
                "status": order.status,
                "total_price": order.total_price,
                "payment_method": order.payment_method,
                "tracking_id": order.tracking_id,
                "shipment_id": order.shipment_id,
                "shipping_address": order.shipping_address,
                "products": order.products,
                "user": {
                    "id": user.id if user else None,
                    "name": getattr(user, "name", "") if user else "",
                    "email": getattr(user, "email", "") if user else "",
                }
            }, status=201)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)



@csrf_exempt
def get_all_orders(request):
    """
    Returns all orders from the database for the Admin Dashboard.
    """
    try:
        # Fetching all orders and including necessary fields
        orders = list(Order.objects.all().values(
        'order_id', 
        
        'user__name',
        'shipment_id', 
        'tracking_id', 
        'total_price', 
        'payment_method', 
        'created_at', 
        'status',
        'products',
        'shipping_address' 
    ))
        return JsonResponse({'success': True, 'data': orders}, safe=False)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_order_by_id(request, pk):
    order = get_object_or_404(Order, order_id=pk)  

    data = {
        "order_id": order.order_id,
        "user_id": order.user.id if order.user else None,  #  include user_id
        "user__name": order.user.name if order.user else None, 
        "payment_method": order.payment_method,
        "shipping_address": order.shipping_address,  # JSONField
        "status": order.status,
        "created_at": order.created_at,
        "shipment_id": order.shipment_id,
        "tracking_id": order.tracking_id,
        "total_price": order.total_price,
        "products": order.products,  #  JSONField

    }

    return JsonResponse(data, safe=False)



@method_decorator(csrf_exempt, name='dispatch')
class OrderStatusUpdateView(View):
    def patch(self, request, order_id, *args, **kwargs):
        try:
            data = json.loads(request.body)
            new_status = data.get("status")

            if new_status not in dict(Order.STATUS_CHOICES):
                return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

            order = Order.objects.get(order_id=order_id)
            order.status = new_status
            order.save()

            # --- STATUS UPDATE EMAIL ---
            shipping_info = order.shipping_address if isinstance(order.shipping_address, dict) else {}
            user_email = shipping_info.get("email")
            user_name = shipping_info.get("name", "Customer")

            if user_email:
                status_labels = {
                    "PENDING":    ("Order Received ⏳",    0),
                    "PROCESSING": ("Order Processing 🔄",  1),
                    "SHIPPED":    ("Your Order is Shipped! 🚚", 2),
                    "DELIVERED":  ("Order Delivered! 🎉",  3),
                    "CANCELLED":  ("Order Cancelled ❌",   -1),
                }
                status_label, tracker_step = status_labels.get(new_status, (new_status, 0))
                subject = f"Rang Raaz Order #{order.order_id} – {status_label}"

                context = {
                    'user_name': user_name,
                    'order_id': order.order_id,
                    'date': order.created_at.strftime('%B %d, %Y'),
                    'new_status': new_status,
                    'status_label': status_label,
                    'tracker_step': tracker_step,
                    'items': [
                        {
                            'name': item.get('name'),
                            'quantity': item.get('quantity'),
                            'price': item.get('price'),
                            'image': item.get('image', ''),
                        }
                        for item in order.products
                    ] if isinstance(order.products, list) else [],
                    'total_amount': order.total_price,
                    'payment_method': "Cash on Delivery" if order.payment_method == "COD" else order.payment_method,
                    'billing_address': {
                        'name': user_name,
                        'street': shipping_info.get("street1", shipping_info.get("street", "N/A")),
                        'city': shipping_info.get("city", "N/A"),
                        'phone': shipping_info.get("phone", "N/A"),
                    }
                }

                html_message = render_to_string('order_email.html', context)
                plain_message = strip_tags(html_message)

                try:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=plain_message,
                        from_email=settings.EMAIL_HOST_USER,
                        to=[user_email],
                    )
                    email.attach_alternative(html_message, "text/html")
                    email.send()
                    print(f"✅ Status update email sent to {user_email} — Status: {new_status}")
                except Exception as mail_err:
                    print(f" Mail error: {str(mail_err)}")
            # --- EMAIL END ---

            return JsonResponse({
                "success": True,
                "message": f"Order {order_id} status updated",
                "order_id": order.order_id,
                "status": order.status,
            }, status=200)

        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Order not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)



def get_weekly_stats(request):
    try:
        last_week = timezone.now() - timedelta(days=7)
        
        weekly_orders = Order.objects.filter(created_at__gte=last_week)
        
        total_weekly = weekly_orders.count()
        pending = weekly_orders.filter(status="PENDING").count()
        processing = weekly_orders.filter(status__in=["PROCESSING", "SHIPPED"]).count()
        delivered = weekly_orders.filter(status="DELIVERED").count()

        return JsonResponse({
            'success': True,
            'weekly_total': total_weekly,
            'weekly_pending': pending,
            'weekly_processing': processing,
            'weekly_delivered': delivered
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    



def get_best_selling_products(request):
    try:
        orders = Order.objects.all()
        product_counts = Counter()

        for order in orders:
            for item in order.products:
                name = item.get('name')
                if name:
                    product_counts[name] += 1

        top_products = product_counts.most_common(5)
        
        labels = [item[0] for item in top_products]
        data = [item[1] for item in top_products]

        return JsonResponse({
            'success': True,
            'labels': labels,
            'data': data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
  
  
  
@csrf_exempt
def update_order_shipment(request, order_id):
    if request.method == "PATCH":
        try:
            data = json.loads(request.body)
            order = Order.objects.get(order_id=order_id)
            order.shipment_id = data.get("shipment_id", order.shipment_id)
            order.tracking_id = data.get("tracking_id", order.tracking_id)
            order.save()
            return JsonResponse({"success": True})
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
 
@csrf_exempt
def delete_order(request, order_id):
    if request.method == "DELETE":
        try:
            order = Order.objects.get(order_id=order_id)
            order.delete()
            return JsonResponse({"success": True, "message": "Order deleted successfully"})
        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Order not found"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid method"}, status=405)   