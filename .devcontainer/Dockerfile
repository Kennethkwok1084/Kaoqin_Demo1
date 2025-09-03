# 使用一个官方的 Python 3.13 镜像，它已经包含了我们所需的工具
FROM python:3.13-slim-bullseye

# 安装 Node.js 和 npm
# 这里我们使用 NodeSource 的官方源，确保安装最新版本
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /workspace

# 安装 Vue CLI
RUN npm install -g @vue/cli

# 暴露你的 Vue 开发服务器可能用到的端口
# 默认是 8080，但如果你用 Vite，可能是 5173 等
EXPOSE 3000 5173 3001