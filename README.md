# 即時聊天應用程式

這是一個基於 **Django** 和 **Django Channels** 構建的即時聊天應用程式，支援多用戶聊天室並使用 WebSocket 傳遞消息。專案包含 REST API 和消息持久化功能，適合本地開發與測試。

## 功能
- 即時消息傳遞（WebSocket 支援）。
- 聊天記錄持久化（預設 SQLite）。
- REST API 供外部發送消息（需認證）。
- 簡單的前端介面（HTML/JavaScript）。
- 環境變數配置（使用 `python-decouple`）。

## 架構圖

```mermaid
graph TD
    A[客戶端瀏覽器] -->|HTTP 請求| B[Django 伺服器]
    B -->|路由| C[urls.py]
    C -->|視圖處理| D[views.py]
    D -->|渲染模板| E[模板：index.html, room.html]
    D -->|封裝回應| F[HttpResponse]
    B -->|TCP 傳輸| A
    A -->|WebSocket| G[Daphne 伺服器]
    G -->|處理| H[ChatConsumer]
    H -->|群組廣播| I[Redis 頻道層]
    I -->|分發| G
    H -->|儲存| J[資料庫]
    D -->|API| K[SendMessageAPI]
    K -->|發送| I
    J -->|加載| E
```

**說明**：
- **HTTP 流程**：
  - `客戶端瀏覽器` 發送 HTTP 請求，`Django 伺服器` 通過 `urls.py` 路由到 `views.py`，渲染 `index.html` 或 `room.html`，生成 `HttpResponse`，並通過 TCP 傳回客戶端。
- **WebSocket 流程**：
  - `Daphne 伺服器` 處理 WebSocket 連線，`ChatConsumer` 管理消息，`Redis 頻道層` 負責廣播，`資料庫` 儲存記錄。
- **API 集成**：`SendMessageAPI` 提供 REST 端點，與 WebSocket 協作。

## 環境要求
- Python 3.10+
- Redis（運行在 `127.0.0.1:6379`）
- Git

## 安裝與運行

1. **克隆倉庫**：
   ```bash
   git clone https://github.com/BpsEason/realtime_chat_project.git
   cd realtime_chat_project
   ```

2. **建立虛擬環境**：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

4. **啟動 Redis**：
   - Ubuntu/Debian：`sudo apt install redis-server`
   - macOS：`brew install redis && brew services start redis`
   - 檢查：`redis-cli ping`（應返回 `PONG`）

5. **配置環境變數**：
   建立 `.env` 檔案：
   ```ini
   SECRET_KEY=your-secure-key-here
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   REDIS_URL=redis://127.0.0.1:6379
   ```
   生成 `SECRET_KEY`：
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

6. **遷移資料庫**：
   ```bash
   python manage.py migrate
   ```

7. **建立超級用戶（可選）**：
   ```bash
   python manage.py createsuperuser
   ```

8. **啟動伺服器**：
   - 終端機 1（WebSocket）：
     ```bash
     daphne -b 0.0.0.0 -p 8000 realtime_chat_project.asgi:application
     ```
   - 終端機 2（HTTP）：
     ```bash
     python manage.py runserver 0.0.0.0:8001
     ```

9. **訪問應用程式**：
   - 打開：`http://127.0.0.1:8001/chat/`
   - WebSocket：`ws://127.0.0.1:8000/ws/chat/<room_name>/`

## 關鍵代碼片段

### 1. WebSocket Consumer (`chat/consumers.py`)
```python
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 獲取聊天室名稱並生成群組名稱
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        # 將當前連線加入聊天室群組
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        # 獲取用戶資訊，匿名時使用預設名稱
        self.user = self.scope['user']
        username = self.user.username if self.user.is_authenticated else "未登入用戶"
        # 接受 WebSocket 連線
        await self.accept()

    async def receive(self, text_data):
        # 解析接收到的 JSON 數據
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        # 獲取發送者用戶名
        username = self.user.username if self.user.is_authenticated else "未登入用戶"
        current_timestamp = timezone.now()
        # 儲存消息到資料庫，區分認證與匿名用戶
        if self.user.is_authenticated:
            ChatMessage.objects.create(room_name=self.room_name, sender=self.user, content=message, timestamp=current_timestamp)
        else:
            ChatMessage.objects.create(room_name=self.room_name, content=message, timestamp=current_timestamp)
        # 將消息廣播到聊天室群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'message': message, 'user': username, 'timestamp': current_timestamp.isoformat()}
        )
```

### 2. REST API (`chat/views.py`)
```python
class SendMessageAPI(APIView):
    permission_classes = [IsAuthenticated]  # 限制僅認證用戶訪問
    def post(self, request, room_name):
        # 獲取請求中的消息內容
        message = request.data.get('message')
        # 驗證消息是否有效
        if not message or not message.strip():
            return Response({"error": "消息內容不可為空"}, status=400)
        current_timestamp = timezone.now()
        # 儲存消息到資料庫
        ChatMessage.objects.create(room_name=room_name, sender=request.user, content=message, timestamp=current_timestamp)
        # 獲取頻道層並同步發送消息到 WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{room_name}',
            {'type': 'chat_message', 'message': message, 'user': request.user.username, 'timestamp': current_timestamp.isoformat()}
        )
        return Response({"status": "成功"}, status=200)
```

### 3. 前端 WebSocket (`chat/templates/chat/room.html`)
```javascript
var wsUrl = 'ws://' + window.location.host + '/ws/chat/' + encodeURIComponent(roomName) + '/';
// 建立 WebSocket 連線
var webSocket = new WebSocket(wsUrl);
// 監聽接收到的消息並更新頁面
webSocket.onmessage = function(e) {
    var data = JSON.parse(e.data);
    appendMessage(data.user, data.message, data.timestamp);
};
// 監聽連線斷開並嘗試重連
webSocket.onclose = function(e) {
    setTimeout(function() { new WebSocket(wsUrl); }, 1000);
};
```

## 常見問題 (FAQ)

### 1. 為什麼選擇 Django Channels 而不是傳統 HTTP 請求？
- **原因**：傳統 HTTP 需輪詢，效率低且延遲高。Django Channels 使用 WebSocket 提供持久連線，實現即時推送。

### 2. Redis 在專案中扮演什麼角色？
- **角色**：Redis 作為頻道層，負責不同 Daphne 實例間的訊息廣播，確保多用戶同步。

### 3. 如何處理 WebSocket 連線的認證與授權？
- **方式**：`AuthMiddlewareStack` 將會話資訊附加到 `scope['user']`，`ChatConsumer` 檢查登入狀態。

### 4. `sync_to_async` 和 `async_to_sync` 的作用？
- **作用**：
  - `sync_to_async`：在異步環境執行同步 ORM 操作。
  - `async_to_sync`：在同步環境呼叫異步操作。

### 5. SendMessageAPI 的用途與 WebSocket 區別？
- **用途**：允許外部系統透過 HTTP POST 發送消息。
- **區別**：REST API 為單次請求，WebSocket 為持久連線；前者非即時，後者適合互動。

### 6. room.html 中 WebSocket 重連機制？
- **實現**：`onclose` 後 1 秒重連，生產環境建議指數退避。

### 7. 如何部署到生產環境？
- **步驟**：
  - **數據庫**：用 PostgreSQL 或 MySQL。
  - **Web 伺服器**：配置 Nginx/Apache 與 SSL。
  - **ASGI 伺服器**：運行 `gunicorn`。
  - **環境變數**：設定 `DEBUG=False`。
  - **日誌**：配置監控。
  - **SSL/TLS**：啟用加密。
  - **持久化**：確保數據持久。
  - **Docker（可選）**：用 Docker Compose。

### 8. Django 伺服器渲染模板後如何回到客戶端？
- **過程**：客戶端發送 HTTP 請求，`urls.py` 路由到 `views.py`，`render` 將 `index.html` 或 `room.html` 渲染成 HTML，封裝成 `HttpResponse`，通過 TCP 傳回瀏覽器顯示。

## 貢獻
1. Fork 倉庫。
2. 建立分支：`git checkout -b feature/name`。
3. 提交：`git commit -m "描述"`。
4. 推送：`git push origin feature/name`。
5. 提交 PR。

## 許可證
採用 MIT 許可證（建議添加 `LICENSE` 檔案）。

## 倉庫連結
[https://github.com/BpsEason/realtime_chat_project](https://github.com/BpsEason/realtime_chat_project)
