# 多阶段构建
FROM python:3.10-slim as builder

# 安装构建工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY backend/ /app/backend/
COPY requirements.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 前端阶段
FROM python:3.10-slim

# 安装 nginx 和运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端文件
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/ /app/backend/
COPY requirements.txt /app/

# 复制前端文件
COPY frontend/ /app/frontend/

# 创建 nginx 配置
RUN cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 8080;
        server_name _;

        root /app/frontend;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /ws {
            proxy_pass http://localhost:8765;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api {
            proxy_pass http://localhost:8765;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

# 暴露端口
EXPOSE 8080 8765

# 启动脚本
RUN echo '#!/bin/bash\n\
echo "Starting Tetris Server..."\n\
cd /app/backend\n\
python3 main.py --host 0.0.0.0 --port 8765 &\n\
nginx -g "daemon off;"\n\
' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]