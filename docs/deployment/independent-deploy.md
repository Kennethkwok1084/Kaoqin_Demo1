# 前后端独立部署指南（Docker + systemctl）

本文档提供两套可独立部署方案：
- 方案 A：Docker（前端/后端分开编排）
- 方案 B：systemctl（后端服务 + Nginx 前端）

## 目录约定
- 项目根目录：`/srv/code/Kaoqin_Demo1`
- 后端：`backend/`
- 前端：`frontend/`
- Docker 分离编排：`deploy/docker/`
- systemd 模板：`deploy/systemd/`

## 方案 A：Docker 独立部署

### 1. 后端独立部署（含 Postgres + Redis）

```bash
cd /srv/code/Kaoqin_Demo1
cp deploy/docker/.env.backend.example deploy/docker/.env.backend
# 按需修改 deploy/docker/.env.backend

docker compose \
  --env-file deploy/docker/.env.backend \
  -f deploy/docker/docker-compose.backend.yml \
  up -d --build
```

健康检查：
```bash
curl -f http://127.0.0.1:8000/health
```

### 2. 前端独立部署（仅前端）

```bash
cd /srv/code/Kaoqin_Demo1
cp deploy/docker/.env.frontend.example deploy/docker/.env.frontend
# 如果后端在其他机器，修改 VITE_API_BASE_URL 为后端公网地址

docker compose \
  --env-file deploy/docker/.env.frontend \
  -f deploy/docker/docker-compose.frontend.yml \
  up -d --build
```

健康检查：
```bash
curl -f http://127.0.0.1/health
```

### 3. 分别升级/重启

后端：
```bash
docker compose --env-file deploy/docker/.env.backend -f deploy/docker/docker-compose.backend.yml pull
docker compose --env-file deploy/docker/.env.backend -f deploy/docker/docker-compose.backend.yml up -d --build
```

前端：
```bash
docker compose --env-file deploy/docker/.env.frontend -f deploy/docker/docker-compose.frontend.yml pull
docker compose --env-file deploy/docker/.env.frontend -f deploy/docker/docker-compose.frontend.yml up -d --build
```

## 方案 B：systemctl 独立部署

### 1. 后端（FastAPI）

### 1.1 准备运行环境
```bash
cd /srv/code/Kaoqin_Demo1/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.2 准备后端环境变量
```bash
cd /srv/code/Kaoqin_Demo1
cp deploy/systemd/backend.env.example deploy/systemd/backend.env
# 按实际数据库、Redis、密钥修改 deploy/systemd/backend.env
```

### 1.3 安装并启动 systemd 服务
```bash
# 如需修改运行用户/路径，请先编辑 deploy/systemd/kaoqin-backend.service
sudo cp deploy/systemd/kaoqin-backend.service /etc/systemd/system/kaoqin-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now kaoqin-backend
```

查看状态：
```bash
sudo systemctl status kaoqin-backend
journalctl -u kaoqin-backend -f
```

### 2. 前端（Nginx）

### 2.1 构建前端静态资源
```bash
cd /srv/code/Kaoqin_Demo1/frontend
npm ci
npm run build
```

### 2.2 配置 Nginx 站点并启用
```bash
sudo cp /srv/code/Kaoqin_Demo1/deploy/systemd/kaoqin-frontend.nginx.conf /etc/nginx/sites-available/kaoqin-frontend.conf
sudo ln -sf /etc/nginx/sites-available/kaoqin-frontend.conf /etc/nginx/sites-enabled/kaoqin-frontend.conf
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

查看状态：
```bash
sudo systemctl status nginx
```

### 3. 分别重启

后端：
```bash
sudo systemctl restart kaoqin-backend
```

前端：
```bash
sudo systemctl reload nginx
```

## 常见配置注意项
- 当前前端镜像已支持构建时注入 `VITE_API_BASE_URL`，用于前后端跨机器部署。
- 如果前端和后端域名不同，后端 `CORS_ORIGINS` 必须包含前端域名。
- Nginx 模板默认把 `/api/` 代理到 `127.0.0.1:8000`，若后端不在本机请修改 `proxy_pass`。
