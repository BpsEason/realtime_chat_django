from django.db import models
from django.contrib.auth.models import User # 導入 Django 內建用戶模型

# 聊天消息模型 (用於存儲歷史記錄)
class ChatMessage(models.Model):
    room_name = models.CharField(max_length=255, db_index=True, verbose_name="聊天室名稱") # 聊天室名稱
    sender = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # 用戶刪除時，消息的發送者欄位設為空
        null=True, 
        blank=True, 
        verbose_name="發送者"
    ) 
    content = models.TextField(verbose_name="消息內容") # 消息內容
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="發送時間") # 發送時間

    class Meta:
        ordering = ['timestamp'] # 依時間戳排序，確保消息順序
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息' # 後台顯示名稱
        # 為 room_name 和 timestamp 組合添加索引，優化歷史消息查詢
        # 可選：如果 room_name 和 timestamp 組合經常被查詢，可以考慮這個索引
        # indexes = [
        #     models.Index(fields=['room_name', 'timestamp']),
        # ]


    def __str__(self):
        sender_name = self.sender.username if self.sender else "匿名"
        return f'{self.room_name} - {sender_name}: {self.content[:50]}...' # 顯示前50字

# 通知模型 (如果需要持久化通知，可以取消註解)
# class Notification(models.Model):
#     recipient = models.ForeignKey(
#         User, 
#         on_delete=models.CASCADE, 
#         related_name='notifications', 
#         verbose_name="接收者"
#     )
#     message = models.TextField(verbose_name="通知內容")
#     is_read = models.BooleanField(default=False, verbose_name="是否已讀")
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
#
#     class Meta:
#         ordering = ['-created_at'] # 最新通知在前
#         verbose_name = '通知'
#         verbose_name_plural = '通知'
#
#     def __str__(self):
#         return f'通知給 {self.recipient.username}: {self.message[:50]}...'
