from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 範例：處理基於房間名的聊天 WebSocket 連線
    # URL 格式：ws://your-domain.com/ws/chat/your_room_name/
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    # 範例：處理通用通知 WebSocket 連線（通常與用戶 ID 綁定）
    # re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),

    # 如果使用 JWT 認證，並且 Token 從 URL 查詢參數傳遞，可能需要這樣的路由
    # re_path(r'ws/chat/(?P<room_name>\w+)/\?token=(?P<token>[^&]+)$', consumers.ChatConsumer.as_asgi()),
]
