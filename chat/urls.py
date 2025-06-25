from django.urls import path, re_path
from . import views

urlpatterns = [
    # 傳統 HTML 頁面路由
    path('', views.index, name='index'), # 聊天室選擇頁
    re_path(r'^(?P<room_name>\w+)/$', views.room, name='room'), # 特定聊天室頁

    # DRF API 路由
    path('api/send_message/<str:room_name>/', views.SendMessageAPI.as_view(), name='send_message_api'),
    # path('api/send_notification/<int:user_id>/', views.SendNotificationAPI.as_view(), name='send_notification_api'),
]
