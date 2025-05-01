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
    update_profile,
    delete_result,
    share_calculation,
    forum_list,
    forum_detail,
    forum_create,
    forum_delete,
    forum_edit,
)

urlpatterns = [
    path('', home_page, name='home'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('databases/', databases, name='databases'),
    path('profile/', profile, name='profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('profile/delete_result/<int:result_id>/', delete_result, name='delete_result'),
    path('graphs/', graph_view, name='graphs'),
    path('calculations/', calculations, name='calculations'),
    path('create-table/', create_table, name='create_table'),
    path('delete-table/<int:pk>/', delete_table, name='delete_table'),
    path('forum/', forum_list, name='forum_list'),
    path('forum/<int:post_id>/', forum_detail, name='forum_detail'),
    path('forum/create/', forum_create, name='forum_create'),
    path('forum/delete/<int:pk>/', forum_delete, name='forum_delete'),
    path('forum/edit/<int:pk>/', forum_edit, name='forum_edit'),
    path('forum/share/<int:result_id>/', share_calculation, name='share_calculation'),
    path('accounts/', include('social_django.urls', namespace='social')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
