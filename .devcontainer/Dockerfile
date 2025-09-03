# 依然使用一个很棒的开发容器基础镜像
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# --- 安装 Python 3.13 ---
# 安装 PPA 管理工具，并添加 deadsnakes PPA (专门提供新版 Python)
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get -y install python3.13 python3.13-venv python3-pip

# --- 安装 Node.js 和 Vue CLI ---
# 安装 Node.js (这里用最新的 LTS 22.x 版本举例)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs

# 安装 Vue 3 项目需要的脚手架 @vue/cli
# npm 会自动装在 /usr/bin/ 下
RUN npm install -g @vue/cli

# --- （可选）清理apt缓存，减小镜像体积 ---
RUN rm -rf /var/lib/apt/lists/*

# 这个镜像不需要自己启动什么服务，所以我们什么都不用加
# 它会默认启动一个 shell，等着 VS Code 连接进来