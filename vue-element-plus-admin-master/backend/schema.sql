CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50),
    email VARCHAR(100),
    department_id INT,
    status INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INT DEFAULT 0,
    sort_order INT DEFAULT 0,
    status INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    status INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parent_id INT DEFAULT 0,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(50),
    path VARCHAR(100),
    component VARCHAR(100),
    permission VARCHAR(100),
    sort_order INT DEFAULT 0,
    status INT DEFAULT 1,
    visible INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS role_menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    menu_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
);

INSERT INTO departments (name, parent_id, sort_order, status) VALUES
('总公司', 0, 1, 1),
('技术部', 1, 1, 1),
('市场部', 1, 2, 1);

INSERT INTO roles (name, code, description, status) VALUES
('超级管理员', 'admin', '拥有所有权限', 1),
('普通用户', 'user', '普通用户权限', 1);

INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) VALUES
(0, '首页', 'vi-ant-design:dashboard-filled', '/dashboard', '#', '', 1, 1, 1),
(1, '分析页', '', '/analysis', 'Dashboard/Analysis', '', 1, 1, 1),
(1, '工作台', '', '/workplace', 'Dashboard/Workplace', '', 2, 1, 1),
(0, '数据查询', 'vi-ant-design:database-outlined', '/data-query', '#', '', 2, 1, 1),
(4, '拆分匹配', '', '/split-match', 'SystemTools/SplitMatch', '', 1, 1, 1),
(4, '详单查询', '', '/detail-query', 'SystemTools/DetailQuery', '', 2, 1, 1),
(0, '系统工具', 'ep:setting', '/system-tools', '#', '', 3, 1, 1),
(7, '同步配置', '', '/sync-config', 'SystemTools/SyncConfig', '', 1, 1, 1),
(7, '同步控制', '', '/sync-control', 'SystemTools/SyncControl', '', 2, 1, 1),
(7, '参数配置', '', '/params-config', 'SystemTools/ParamsConfig', '', 3, 1, 1),
(0, '系统管理', 'vi-eos-icons:role-binding', '/authorization', '#', '', 4, 1, 1),
(11, '部门管理', '', '/department', 'Authorization/Department/Department', '', 1, 1, 1),
(11, '用户管理', '', '/user', 'Authorization/User/User', '', 2, 1, 1),
(11, '菜单管理', '', '/menu', 'Authorization/Menu/Menu', '', 3, 1, 1),
(11, '角色管理', '', '/role', 'Authorization/Role/Role', '', 4, 1, 1);

INSERT INTO user_roles (user_id, role_id) VALUES
(1, 1);

INSERT INTO role_menus (role_id, menu_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15);
