# 生产环境部署指南

## 1. 环境准备

### 1.1 服务器要求

| 组件 | 版本/要求 | 备注 |
|------|-----------|------|
| 操作系统 | Ubuntu 22.04.4 LTS 或 CentOS 7.9.2009 | 推荐Ubuntu 22.04.4 LTS |
| Python | 3.7+ | 已安装 |
| Node.js | 18.0+ | 仅前端构建需要 |
| Nginx | 1.18+ | 用于前端静态文件服务 |
| 宝塔面板 | v8.1.0+ | 已安装 |
| 端口 | 4000 (前端), 8000 (后端) | 需确保端口未被占用 |

### 1.2 网络要求
- 服务器需能访问互联网（用于安装依赖）
- 或准备离线依赖包

## 2. 部署步骤

### 2.1 前端部署

#### 2.1.1 安装Nginx
```bash
# Ubuntu
apt update
apt install nginx -y

# CentOS
yum install nginx -y
```

#### 2.1.2 配置Nginx
1. 创建前端配置文件
```bash
# Ubuntu
vim /etc/nginx/sites-available/frontend

# CentOS
vim /etc/nginx/conf.d/frontend.conf
```

2. 添加以下配置：
```nginx
server {
    listen 4000;
    server_name localhost;

    root /var/www/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. 启用配置并重启Nginx
```bash
# Ubuntu
ln -s /etc/nginx/sites-available/frontend /etc/nginx/sites-enabled/

# 重启Nginx
systemctl restart nginx
systemctl enable nginx
```

#### 2.1.3 部署前端静态文件
1. 复制前端构建产物到Nginx目录
```bash
mkdir -p /var/www/frontend
cp -r /path/to/newversion/frontend/* /var/www/frontend/
```

2. 设置文件权限
```bash
chown -R www-data:www-data /var/www/frontend
```

### 2.2 后端部署

#### 2.2.1 安装Python依赖
1. 进入后端目录
```bash
cd /path/to/newversion/backend
```

2. 安装依赖
```bash
pip3 install -r requirements.txt
```

#### 2.2.2 配置后端服务
1. 修改配置文件（如需）
```bash
vim config.ini
```

2. 创建systemd服务文件
```bash
vim /etc/systemd/system/backend.service
```

3. 添加以下内容：
```ini
[Unit]
Description=FastAPI Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/newversion/backend
ExecStart=/usr/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Restart=always

[Install]
WantedBy=multi-user.target
```

4. 启动并启用服务
```bash
systemctl daemon-reload
systemctl start backend
systemctl enable backend
```

### 2.3 防火墙配置

#### 2.3.1 开放端口
```bash
# Ubuntu
ufw allow 4000
tufw allow 8000
ufw enable

# CentOS
firewall-cmd --permanent --add-port=4000/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

### 2.4 宝塔面板配置

#### 2.4.1 添加网站
1. 登录宝塔面板
2. 点击「网站」→「添加站点」
3. 域名填写服务器IP地址
4. 网站目录选择 `/var/www/frontend`
5. 端口填写4000
6. 点击「提交」

#### 2.4.2 添加反向代理
1. 点击刚创建的网站
2. 点击「反向代理」
3. 点击「添加反向代理」
4. 填写以下信息：
   - 代理名称：API
   - 目标URL：`http://127.0.0.1:8000`
   - 发送域名：`$host`
   - 启用WebSocket
5. 点击「提交」

## 3. 离线环境部署

### 3.1 前端离线部署
1. 已构建的前端产物已包含所有依赖，直接复制到服务器即可

### 3.2 后端离线部署
1. 提前下载Python依赖包
```bash
# 在有网络的环境中
pip3 download -r requirements.txt -d ./dependencies
```

2. 将依赖包和代码一起复制到离线服务器

3. 离线安装依赖
```bash
pip3 install --no-index --find-links=./dependencies -r requirements.txt
```

## 4. 服务管理

### 4.1 启动服务
```bash
# 前端（Nginx）
systemctl start nginx

# 后端
systemctl start backend
```

### 4.2 停止服务
```bash
# 前端（Nginx）
systemctl stop nginx

# 后端
systemctl stop backend
```

### 4.3 重启服务
```bash
# 前端（Nginx）
systemctl restart nginx

# 后端
systemctl restart backend
```

### 4.4 查看服务状态
```bash
# 前端（Nginx）
systemctl status nginx

# 后端
systemctl status backend
```

## 5. 故障排查

### 5.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 前端无法访问 | Nginx未启动或配置错误 | 检查Nginx状态和配置 |
| 后端API无法访问 | 后端服务未启动或端口被占用 | 检查后端服务状态和端口占用 |
| 数据库连接失败 | 数据库配置错误或数据库未启动 | 检查数据库配置和状态 |
| 502 Bad Gateway | 后端服务未启动或反向代理配置错误 | 检查后端服务状态和反向代理配置 |

### 5.2 日志查看

```bash
# Nginx日志
cat /var/log/nginx/error.log

# 后端日志
journalctl -u backend

# 后端应用日志
cat /path/to/newversion/backend/logs/app.log
cat /path/to/newversion/backend/logs/error.log
```

## 6. 性能优化

### 6.1 前端优化
- 启用Nginx gzip压缩
- 配置浏览器缓存
- 使用CDN（如果有条件）

### 6.2 后端优化
- 使用进程管理器（如Gunicorn）
- 配置适当的进程数和线程数
- 启用数据库连接池
- 优化SQL查询

## 7. 安全配置

### 7.1 Nginx安全配置
- 禁用服务器版本信息
- 配置HTTPS（如果有SSL证书）
- 设置适当的CORS策略

### 7.2 后端安全配置
- 使用环境变量存储敏感信息
- 配置适当的错误处理
- 实现请求速率限制
- 定期更新依赖包

## 8. 部署验证

### 8.1 前端验证
1. 访问 `http://服务器IP:4000`
2. 检查页面是否正常加载
3. 测试所有功能是否正常

### 8.2 后端验证
1. 访问 `http://服务器IP:8000/docs`
2. 检查API文档是否正常显示
3. 测试API接口是否正常响应

## 9. 维护指南

### 9.1 版本更新
1. 停止服务
2. 备份现有代码
3. 复制新的构建产物
4. 安装新的依赖（如需）
5. 启动服务
6. 验证功能

### 9.2 定期维护
- 检查服务器资源使用情况
- 查看日志文件，及时发现问题
- 定期备份数据
- 更新系统和依赖包

## 10. 总结

本部署指南提供了详细的生产环境部署步骤，包括前端和后端的部署、配置和维护。按照本指南操作，可以确保项目在生产环境中稳定运行。

如需进一步的技术支持，请联系开发团队。