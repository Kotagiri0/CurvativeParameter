from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from main.views import (
    home_page,
    register,
    login_user,
    logout_user,
    databases,
    graph_view,
    calculations,
    create_table,
    delete_table,
    profile,
    update_email  # Добавляем update_email
)

urlpatterns = [
    path('', home_page, name='home'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('databases/', databases, name='databases'),
    path('profile/', profile, name='profile'),
    path('graphs/', graph_view, name='graphs'),
    path('calculations/', calculations, name='calculations'),
    path('create-table/', create_table, name='create_table'),
    path('delete-table/<int:pk>/', delete_table, name='delete_table'),
    path('update-email/', update_email, name='update_email'),  # Новый маршрут
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)