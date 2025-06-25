import json
import datetime
import logging # 導入 logging 模組
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User # 確保導入 User 模型
from .models import ChatMessage # 確保導入 ChatMessage 模型

# 配置日誌記錄器
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        self.user = self.scope['user']
        # 如果用戶已認證，使用其用戶名；否則，顯示為 '未登入用戶'
        username = await sync_to_async(lambda: self.user.username)() if self.user.is_authenticated else "未登入用戶"
        logger.info(f"用戶 '{username}' 連線到房間: {self.room_name}")

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        username = await sync_to_async(lambda: self.user.username)() if self.user.is_authenticated else "未登入用戶"
        logger.info(f"用戶 '{username}' 從房間斷開: {self.room_name} 代碼: {close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message')

            # 後端驗證房間名稱格式 (範例：只允許字母數字)
            import re
            valid_room_pattern = re.compile(r'^[a-zA-Z0-9_]+$') # 允許字母、數字、底線
            if not valid_room_pattern.match(self.room_name):
                logger.warning(f"Consumer: 檢測到無效房間名稱格式: {self.room_name}，拒絕處理消息。")
                await self.send(text_data=json.dumps({"error": "房間名稱格式無效。"}))
                return

            if not message or not isinstance(message, str) or not message.strip():
                logger.warning("收到空消息或無效消息。")
                await self.send(text_data=json.dumps({"error": "消息內容為空或格式無效。"})) # 前端提示
                return

            username = await sync_to_async(lambda: self.user.username)() if self.user.is_authenticated else "未登入用戶"
            
            # 使用 Django 的時區感知時間
            from django.utils import timezone
            current_timestamp = timezone.now()

            # 將消息存儲到數據庫
            # 確保 ChatMessage 模型已在 models.py 中啟用
            try:
                # 只有當用戶已認證時，才將其作為 sender 儲存
                if self.user.is_authenticated:
                    await sync_to_async(ChatMessage.objects.create)(
                        room_name=self.room_name,
                        sender=self.user,
                        content=message,
                        timestamp=current_timestamp
                    )
                else:
                    # 如果未登入，sender 欄位設為 None (如果模型允許 null=True)
                    await sync_to_async(ChatMessage.objects.create)(
                        room_name=self.room_name,
                        content=message,
                        timestamp=current_timestamp
                    )
                logger.debug(f"消息 '{message}' 已儲存到資料庫。")
            except Exception as e:
                logger.error(f"保存消息到數據庫時發生錯誤: {e}")
                # 即使資料庫儲存失敗，仍嘗試發送到 WebSocket，保證即時性
                # 但生產環境應有更完善的錯誤處理和重試機制

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', 
                    'message': message,
                    'user': username,
                    'timestamp': current_timestamp.isoformat(), # 使用 ISO 格式方便前端解析
                }
            )
        except json.JSONDecodeError:
            logger.error("收到非 JSON 格式的數據。")
            await self.send(text_data=json.dumps({"error": "Invalid JSON format."}))
        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {e}")
            await self.send(text_data=json.dumps({"error": "Server error processing message."}))


    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        timestamp = event.get('timestamp', '時間未知')

        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'timestamp': timestamp,
        }))

# 範例：通用通知 Consumer
# class NotificationConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope['user']
#         if not self.user.is_authenticated:
#             await self.close() # 未認證用戶不允許連接
#             return
#         
#         self.user_group_name = f'user_notifications_{self.user.id}'
#         await self.channel_layer.group_add(
#             self.user_group_name,
#             self.channel_name
#         )
#         logger.info(f"用戶 '{self.user.username}' 連線到個人通知頻道。")
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         if self.user.is_authenticated:
#             await self.channel_layer.group_discard(
#                 self.user_group_name,
#                 self.channel_name
#             )
#             logger.info(f"用戶 '{self.user.username}' 從個人通知頻道斷開。")
#
#     async def send_notification(self, event):
#         message = event['message']
#
#         await self.send(text_data=json.dumps({
#             'type': 'notification',
#             'message': message,
#             'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         }))
