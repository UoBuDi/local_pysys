-- 权限粒度优化数据库迁移脚本
-- 执行时间：2026-03-09
-- 目的：实现细粒度权限控制，支持到操作级别的权限管理

-- 1. 扩展菜单表，添加操作类型字段
ALTER TABLE menus ADD COLUMN operations TEXT COMMENT '操作类型，JSON格式，如["add","edit","delete"]';

-- 2. 创建权限点表
CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码',
    name VARCHAR(50) NOT NULL COMMENT '权限名称',
    module VARCHAR(50) NOT NULL COMMENT '所属模块',
    resource VARCHAR(50) NOT NULL COMMENT '资源类型',
    operation VARCHAR(50) NOT NULL COMMENT '操作类型',
    description VARCHAR(200) COMMENT '权限描述',
    status INT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_module_resource (module, resource, operation),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限点表';

-- 3. 创建角色-权限关联表
CREATE TABLE role_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL COMMENT '角色ID',
    permission_id INT NOT NULL COMMENT '权限点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色-权限关联表';

-- 4. 初始化权限点数据
INSERT IGNORE INTO permissions (code, name, module, resource, operation, description) VALUES
('system:user:add', '新增用户', 'system', 'user', 'add', '允许新增用户'),
('system:user:edit', '编辑用户', 'system', 'user', 'edit', '允许编辑用户信息'),
('system:user:delete', '删除用户', 'system', 'user', 'delete', '允许删除用户'),
('system:user:export', '导出用户', 'system', 'user', 'export', '允许导出用户数据'),
('system:user:assign', '分配角色', 'system', 'user', 'assign', '允许为用户分配角色'),
('system:user:view', '查看用户', 'system', 'user', 'view', '允许查看用户列表'),
('system:role:add', '新增角色', 'system', 'role', 'add', '允许新增角色'),
('system:role:edit', '编辑角色', 'system', 'role', 'edit', '允许编辑角色信息'),
('system:role:delete', '删除角色', 'system', 'role', 'delete', '允许删除角色'),
('system:role:assign', '分配菜单', 'system', 'role', 'assign', '允许为角色分配菜单'),
('system:role:view', '查看角色', 'system', 'role', 'view', '允许查看角色列表'),
('system:menu:add', '新增菜单', 'system', 'menu', 'add', '允许新增菜单'),
('system:menu:edit', '编辑菜单', 'system', 'menu', 'edit', '允许编辑菜单信息'),
('system:menu:delete', '删除菜单', 'system', 'menu', 'delete', '允许删除菜单'),
('system:menu:view', '查看菜单', 'system', 'menu', 'view', '允许查看菜单列表'),
('system:dept:add', '新增部门', 'system', 'dept', 'add', '允许新增部门'),
('system:dept:edit', '编辑部门', 'system', 'dept', 'edit', '允许编辑部门信息'),
('system:dept:delete', '删除部门', 'system', 'dept', 'delete', '允许删除部门'),
('system:dept:view', '查看部门', 'system', 'dept', 'view', '允许查看部门列表'),
('data:query:all', '查询全部数据', 'data', 'query', 'all', '允许查询全部数据'),
('data:query:own', '查询自己数据', 'data', 'query', 'own', '仅允许查询自己的数据'),
('data:query:dept', '查询部门数据', 'data', 'query', 'dept', '允许查询本部门数据'),
('data:export:all', '导出全部数据', 'data', 'export', 'all', '允许导出全部数据'),
('data:export:own', '导出自己数据', 'data', 'export', 'own', '仅允许导出自己的数据'),
('data:export:dept', '导出部门数据', 'data', 'export', 'dept', '允许导出本部门数据'),
('system:sync:config', '同步配置', 'system', 'sync', 'config', '允许配置同步参数'),
('system:sync:control', '同步控制', 'system', 'sync', 'control', '允许控制同步任务'),
('system:sync:view', '查看同步', 'system', 'sync', 'view', '允许查看同步状态'),
('system:params:config', '参数配置', 'system', 'params', 'config', '允许配置系统参数'),
('system:params:view', '查看参数', 'system', 'params', 'view', '允许查看系统参数'),
('system:debug:view', '查看调试信息', 'system', 'debug', 'view', '允许查看调试信息'),
('system:debug:export', '导出调试数据', 'system', 'debug', 'export', '允许导出调试数据');

-- 5. 为超级管理员角色分配所有权限
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions WHERE status = 1;

-- 6. 更新菜单表的权限标识（使用新的细粒度权限）
UPDATE menus SET permission = 'system:user:view' WHERE id = 12;
UPDATE menus SET permission = 'system:role:view' WHERE id = 14;
UPDATE menus SET permission = 'system:menu:view' WHERE id = 13;
UPDATE menus SET permission = 'system:dept:view' WHERE id = 11;
UPDATE menus SET permission = 'data:query:all' WHERE id = 5;
UPDATE menus SET permission = 'data:query:all' WHERE id = 6;
UPDATE menus SET permission = 'system:sync:config' WHERE id = 8;
UPDATE menus SET permission = 'system:sync:control' WHERE id = 9;
UPDATE menus SET permission = 'system:params:config' WHERE id = 10;

-- 7. 创建视图：用户权限视图（用于快速查询用户的所有权限）
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id AS user_id,
    u.username,
    p.code AS permission_code,
    p.name AS permission_name,
    p.module,
    p.resource,
    p.operation,
    r.id AS role_id,
    r.name AS role_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE p.status = 1 AND r.status = 1;

-- 8. 创建索引优化查询性能
CREATE INDEX idx_user_permissions_user_id ON v_user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission_code ON v_user_permissions(permission_code);

-- 迁移完成标记
INSERT IGNORE INTO migration_history (version, description, executed_at) 
VALUES ('1.0.0', '权限粒度优化：创建权限点表、角色-权限关联表，初始化权限数据', NOW());
