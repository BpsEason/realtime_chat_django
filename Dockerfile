# realtime_chat_project/Dockerfile

# 使用 Python 官方映像檔作為基礎，選擇一個穩定的版本
FROM python:3.10-slim-buster

# 設定工作目錄
WORKDIR /app

# 設定環境變數，讓 Python 輸出直接顯示，不緩衝
ENV PYTHONUNBUFFERED 1

# 複製 requirements.txt 到工作目錄
COPY requirements.txt /app/

# 安裝 Python 依賴
# 使用 --no-cache-dir 避免生成緩存，減少映像檔大小
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案程式碼到工作目錄
COPY . /app/

# 收集靜態文件 (生產環境建議在構建時就收集)
# 如果您在開發環境不希望每次重構都執行，可以移到 docker-compose exec
RUN python manage.py collectstatic --noinput

# 只需暴露 Daphne 將運行的 8000 埠
EXPOSE 8000

# 預設啟動命令改為 daphne，更具代表性，並且使用 PROJECT_NAME
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "realtime_chat_project.asgi:application"]
