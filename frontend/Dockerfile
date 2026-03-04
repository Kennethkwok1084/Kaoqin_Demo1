# 多阶段构建 - 前端应用
FROM node:18-alpine as builder

# 设置构建参数
ARG VERSION=dev
ARG BUILD_DATE

# 设置工作目录
WORKDIR /app

# 复制包配置文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 设置构建环境变量
ENV NODE_ENV=production
ENV VITE_APP_VERSION=${VERSION}
ENV VITE_BUILD_DATE=${BUILD_DATE}
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_TITLE=考勤管理系统
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_TITLE=${VITE_APP_TITLE}

# 构建应用
RUN npm run build

# 生产运行阶段
FROM nginx:1.25-alpine as runtime

# 设置元数据标签
LABEL version="${VERSION}" \
      build-date="${BUILD_DATE}" \
      description="Attendance Management System Frontend" \
      maintainer="Attendance Team"

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从builder阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建非root用户
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# 设置正确的权限
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# 切换到非root用户
USER nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
