import os
from django.core.asgi import get_asgi_application

# 設置 Django 應用，確保在導入 Channels 相關組件前 Django 環境已初始化
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime_chat_project.settings')
django_asgi_app = get_asgi_application() # Django 的 HTTP 處理部分

# 在此之後導入 Channels 相關模組
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# 從你的 App 導入 WebSocket 路由定義
from chat import routing

# 根 ASGI 應用，根據協議類型分發請求
application = ProtocolTypeRouter({
    # HTTP 請求會由 Django 的 WSGI/ASGI 處理器處理
    "http": django_asgi_app, 

    # WebSocket 請求會通過 Channels 處理
    "websocket": AllowedHostsOriginValidator( # 確保 WebSocket 連線來自允許的主機
        AuthMiddlewareStack( # 為 WebSocket 連線提供 Django 的認證功能 (如 Session 認證)
            URLRouter( # 將 WebSocket URL 路由到對應的 Consumer
                routing.websocket_urlpatterns
            )
        )
    ),
})
