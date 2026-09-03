# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Customer
import json
from django.db import transaction
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from django.conf import settings


@csrf_exempt
def signup(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            phone = data.get('phone')
            password = data.get('password')
            address = data.get('address')
            role = data.get('role', 'customer').lower()

            if Customer.objects.filter(phone=phone).exists():
                return JsonResponse({'status': 'error', 'message': 'User already exists'}, status=400)

            
            user = Customer.objects.create(
                name=name,
                phone=phone,
                password=password,
                address=address,
                role=role
            )

            return JsonResponse({
                'status': 'success',
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'phone': user.phone,
                    'address': user.address,
                    'role': user.role
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def signin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            password = data.get('password')

            user = Customer.objects.filter(phone=phone, password=password).first()

            if user:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'phone': user.phone,
                        'address': user.address,
                        'role': user.role
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

@csrf_exempt
def add_admin(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)

      

        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        address = data.get('address', '')

        if not name or not phone or not password:
            return JsonResponse({'status': 'error', 'message': 'Name, phone and password are required'}, status=400)

        if Customer.objects.filter(phone=phone).exists():
            return JsonResponse({'status': 'error', 'message': 'Phone already in use'}, status=400)

        user = Customer.objects.create(
            name=name,
            phone=phone,
            password=password,  
            address=address,
            role='admin',         
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Admin created successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'address': user.address,
                'role': user.role,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def google_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            token = data.get('token')

            if not token:
                return JsonResponse({'status': 'error', 'message': 'Token missing'}, status=400)

            idinfo = id_token.verify_oauth2_token(token, grequests.Request(), settings.GOOGLE_CLIENT_ID)
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            name = idinfo.get('name')

            print(f"[GOOGLE VERIFIED]: {name} ({email})")

            user = Customer.objects.filter(google_id=google_id).first()

            if not user:
                user = Customer.objects.filter(email=email).first()
                if user:
                    user.google_id = google_id
                    user.save()
                    print(f"[GOOGLE LINK]: Linked to existing user {email}")
                else:
                    user = Customer.objects.create(
                        name=name,
                        email=email,
                        google_id=google_id,
                        password="GOOGLE",
                        address="",
                        role="customer"
                    )
                    print(f"[GOOGLE REGISTER]: New user created {email}")

            return JsonResponse({
                'status': 'success',
                'message': 'Google login successful',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role,
                }
            })

        except ValueError as e:
            print(f"[GOOGLE ERROR]: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Invalid Google token'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def getallusers(request):
    members = Customer.objects.all()
    data = [
        {
            "id": m.id,
            "name": m.name,
            "address": m.address,
            "role": m.role
        }
        for m in members
    ]
    return JsonResponse({"data": data})


@csrf_exempt
def update_role(request, pk):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_role = data.get("role")

            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(id=pk)
                customer.role = new_role
                customer.save()

            return JsonResponse({"success": True, "message": "Role updated"})
        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid method"})


@csrf_exempt
def get_roles(request):
    if request.method == "GET":
        roles = [
            {"id": role, "role": label}
            for role, label in Customer.ROLE_CHOICES
        ]
        return JsonResponse(roles, safe=False)


@csrf_exempt
def delete_user(request, pk):
    if request.method == "DELETE":
        try:
            customer = Customer.objects.get(id=pk)
            customer.delete()
            return JsonResponse({"success": True, "message": "User deleted"})
        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid method"})
