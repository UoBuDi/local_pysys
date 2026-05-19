-- 添加角色
INSERT INTO roles (name, code, description, status) VALUES 
('超级管理员', 'super_admin', '拥有系统所有权限', 1),
('管理员', 'admin', '拥有系统管理权限', 1),
('操作员', 'operator', '拥有基本操作权限', 1),
('访客', 'guest', '仅拥有查看权限', 1) ON DUPLICATE KEY UPDATE name = VALUES(name), description = VALUES(description), status = VALUES(status);

-- 检查admin用户是否存在，如果不存在则创建
INSERT INTO users (username, password, nickname, email, status) 
SELECT 'admin', '$2b$12$d6YbFyJZ3CwK3vY7vU1nL2oP3iQ4wE5rT6yU7iO8pI9uY0tR1eW2qA3sZ4x5cV6bN7m8n9b0v1c2x3z4a5s6d7f8g9h0j1k2l3m4n5b6v7c8x9z0a1s2d3f4g5h6j7k8l9z0x1c2v3b4n5m6n7b8v9c0x1s2d3f4g5h6j7k8l9z0', '系统管理员', 'admin@example.com', 1
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- 将admin用户绑定为超级管理员
INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id FROM users u, roles r 
WHERE u.username = 'admin' AND r.code = 'super_admin' 
ON DUPLICATE KEY UPDATE user_id = VALUES(user_id), role_id = VALUES(role_id);
