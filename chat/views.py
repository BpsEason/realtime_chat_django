from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated # 引入認證相關類
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging # 導入 logging 模組
import re # 導入正則表達式模組
from django.utils import timezone # 導入時區感知時間

# 導入模型和用戶模型
from .models import ChatMessage 
from django.contrib.auth.models import User

# 配置日誌記錄器
logger = logging.getLogger(__name__)

# Django 傳統視圖，用於渲染 HTML 頁面
def index(request):
    """
    渲染聊天室選擇頁面。
    """
    return render(request, 'chat/index.html')

def room(request, room_name):
    """
    渲染特定聊天室頁面，並加載歷史消息。
    """
    # 後端驗證房間名稱格式
    valid_room_pattern = re.compile(r'^[a-zA-Z0-9_]+$') # 允許字母、數字、底線
    if not valid_room_pattern.match(room_name):
        logger.warning(f"View: 檢測到無效房間名稱格式: {room_name}，顯示錯誤頁面。")
        # 可以建立一個專門的錯誤頁面或重定向
        return render(request, 'chat/invalid_room.html', {'error_message': '聊天室名稱格式無效。'}) 

    messages = []
    try:
        # 加載歷史消息 (已在 models.py 中啟用 ChatMessage)
        # 獲取最近的 100 條消息
        messages = ChatMessage.objects.filter(room_name=room_name).order_by('timestamp').select_related('sender')[:100]
    except Exception as e:
        logger.error(f"加載歷史消息時發生錯誤: {e}")
            
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'messages': messages, # 將消息傳遞給模板
    })

# Django REST Framework API 視圖：透過 HTTP 發送消息到 WebSocket 頻道
class SendMessageAPI(APIView):
    # 預設需要認證用戶才能透過 API 發送訊息，提高安全性
    permission_classes = [IsAuthenticated] 

    def post(self, request, room_name, *args, **kwargs):
        """
        接收 HTTP POST 請求，將消息發送到指定房間的 WebSocket 頻道層。
        """
        # 後端驗證房間名稱格式
        valid_room_pattern = re.compile(r'^[a-zA-Z0-9_]+$') # 允許字母、數字、底線
        if not valid_room_pattern.match(room_name):
            logger.warning(f"API: 檢測到無效房間名稱格式: {room_name}。")
            return Response({"error": "房間名稱格式無效。"}, status=status.HTTP_400_BAD_REQUEST)

        message_content = request.data.get('message')
        if not message_content or not isinstance(message_content, str) or not message_content.strip():
            logger.warning("API 收到空消息或無效消息。")
            return Response({"error": "消息內容為必填項且不能為空。"}, status=status.HTTP_400_BAD_REQUEST)

        channel_layer = get_channel_layer()
        room_group_name = f'chat_{room_name}'
        
        user_display_name = request.user.username if request.user.is_authenticated else "API 發送者"

        current_timestamp = timezone.now()

        # 將消息存儲到數據庫 (ChatMessage 模型已啟用)
        try:
            ChatMessage.objects.create(
                room_name=room_name, 
                sender=request.user, # sender 欄位現在要求登入用戶
                content=message_content, 
                timestamp=current_timestamp
            )
            logger.debug(f"API 發送消息 '{message_content}' 已儲存到資料庫。")
        except Exception as e:
            logger.error(f"API 保存消息到數據庫時發生錯誤: {e}")
            # 即使資料庫儲存失敗，仍嘗試發送到 WebSocket，保證即時性
            # 但生產環境應有更完善的錯誤處理和重試機制

        # 使用 async_to_sync 將異步的 channel_layer.group_send 轉為同步執行
        # 這會觸發 ChatConsumer 中的 chat_message 方法
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'chat_message', 
                'message': message_content,
                'user': user_display_name,
                'timestamp': current_timestamp.isoformat(), # 使用 ISO 格式方便前端解析
            }
        )
        return Response({"status": "消息已成功發送到 WebSocket 頻道。"}, status=status.HTTP_200_OK)

# 範例：透過 HTTP API 發送個人通知
# class SendNotificationAPI(APIView):
#     permission_classes = [IsAuthenticated] # 只有認證用戶才能發送通知

#     def post(self, request, user_id, *args, **kwargs):
#         notification_message = request.data.get('message')
#         if not notification_message or not isinstance(notification_message, str) or not notification_message.strip():
#             return Response({"error": "通知消息內容為必填項且不能為空。"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             recipient_user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return Response({"error": "接收者用戶不存在。"}, status=status.HTTP_404_NOT_FOUND)

#         channel_layer = get_channel_layer()
#         user_group_name = f'user_notifications_{recipient_user.id}' # 需與 NotificationConsumer 中的 group_name 一致

#         # 可選：將通知存儲到數據庫 (需在 models.py 中取消註解 Notification)
#         # try:
#         #     Notification.objects.create(recipient=recipient_user, message=notification_message)
#         # except Exception as e:
#         #     logger.error(f"保存通知到數據庫時發生錯誤: {e}")

#         # 發送通知到指定用戶的頻道
#         async_to_sync(channel_layer.group_send)(
#             user_group_name,
#             {
#                 'type': 'send_notification', # 這會觸發 NotificationConsumer 中的 send_notification 方法
#                 'message': notification_message,
#             }
#         )
#         return Response({"status": "通知已成功發送到用戶頻道。"}, status=status.HTTP_200_OK)

