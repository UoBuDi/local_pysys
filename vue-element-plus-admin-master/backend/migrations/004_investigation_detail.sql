-- 追查详单功能数据库迁移脚本
-- 执行时间：2026-06-16
-- 目的：创建追查详单表、菜单、权限点

-- 1. 创建追查详单表
CREATE TABLE IF NOT EXISTS investigation_details (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    pass_id VARCHAR(100) NOT NULL COMMENT '通行标识ID',
    plate_number VARCHAR(50) NOT NULL COMMENT '车牌号码',
    add_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    created_by VARCHAR(50) NOT NULL COMMENT '创建人（加入追查的用户名）',
    review_result VARCHAR(200) DEFAULT NULL COMMENT '复核结果（最多200字符）',
    reviewed_by VARCHAR(50) DEFAULT NULL COMMENT '复核人（填写复核结果时的用户名）',
    review_time DATETIME DEFAULT NULL COMMENT '复核时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    INDEX idx_pass_id (pass_id),
    INDEX idx_plate_number (plate_number),
    INDEX idx_created_by (created_by),
    INDEX idx_add_time (add_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='追查详单表';

-- 2. 插入菜单记录（数据查询菜单的parent_id=4）
INSERT INTO menus (parent_id, name, icon, path, component, permission, sort_order, status, visible) 
VALUES (4, '追查详单', 'vi-ant-design:search-outlined', '/data-query/investigation-detail', 'SystemTools/InvestigationDetail', 'investigation:view', 4, 1, 1);

-- 3. 插入权限点记录
INSERT IGNORE INTO permissions (code, name, module, resource, operation, description, status) VALUES
('investigation:view', '查看追查详单', 'investigation', 'detail', 'view', '允许查看追查详单列表', 1),
('investigation:add', '加入追查', 'investigation', 'detail', 'add', '允许将数据加入追查详单', 1),
('investigation:review', '复核追查详单', 'investigation', 'detail', 'review', '允许填写复核结果', 1),
('investigation:delete', '删除追查详单', 'investigation', 'detail', 'delete', '允许删除追查详单记录', 1),
('investigation:export', '导出追查详单', 'investigation', 'detail', 'export', '允许导出追查详单数据', 1);

-- 4. 为超级管理员角色（role_id=1）分配新权限
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions WHERE code LIKE 'investigation:%' AND status = 1;

-- 5. 为新菜单分配给超级管理员角色
INSERT IGNORE INTO role_menus (role_id, menu_id)
SELECT 1, id FROM menus WHERE name = '追查详单';

-- 迁移完成标记
INSERT IGNORE INTO migration_history (version, description, executed_at) 
VALUES ('1.1.0', '追查详单功能：创建investigation_details表、菜单、权限点', NOW())
ON DUPLICATE KEY UPDATE description = '追查详单功能：创建investigation_details表、菜单、权限点';