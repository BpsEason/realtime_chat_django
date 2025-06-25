"""
URL configuration for realtime_chat_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include # 導入 include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')), # 包含你的聊天應用 URL
    # 如果有其他 API 或 App，可以在這裡繼續添加
    # path('api-auth/', include('rest_framework.urls')), # DRF 內建的登入/登出 API (可選)
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # JWT Token 獲取
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # JWT Token 刷新
]
