from django.urls import path
from .views import signin,signup,getallusers,update_role,delete_user,google_login

urlpatterns = [
    path('signup/',signup, name='signup'),
    path('signin/', signin, name='signin'),
    path('getallusers/', getallusers,name='all_data'),
    path('update-role/<int:pk>/', update_role, name='update_role'), 
    path('delete-user/<int:pk>/', delete_user, name='delete_user'),
     path('google-login/', google_login, name='google_login'),


]
