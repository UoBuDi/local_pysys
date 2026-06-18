-- Chat.vue 功能增强迁移脚本
-- CH-01~CH-08: 搜索、群聊管理、撤回、图片、已读回执、导出、置顶/免打扰、@提及

-- 1. chat_messages 新增字段
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS is_recalled TINYINT NOT NULL DEFAULT 0 COMMENT '是否已撤回: 0否 1是';
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS mentioned_user_ids JSON DEFAULT NULL COMMENT '@提及的用户ID列表';
ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS file_name VARCHAR(500) DEFAULT NULL COMMENT '文件/图片原始文件名';

-- 2. chat_sessions 新增字段
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_pinned TINYINT NOT NULL DEFAULT 0 COMMENT '是否置顶: 0否 1是';
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_muted TINYINT NOT NULL DEFAULT 0 COMMENT '是否免打扰: 0否 1是';

-- 3. 群聊成员表
CREATE TABLE IF NOT EXISTS chat_group_members (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    room_id VARCHAR(100) NOT NULL COMMENT '群聊房间ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role VARCHAR(20) NOT NULL DEFAULT 'member' COMMENT '角色: owner/admin/member',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    UNIQUE KEY uk_room_user (room_id, user_id),
    INDEX idx_room_id (room_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='群聊成员表';

-- 4. 消息已读记录表
CREATE TABLE IF NOT EXISTS chat_message_read (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id BIGINT NOT NULL COMMENT '消息ID',
    user_id INT NOT NULL COMMENT '已读用户ID',
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '已读时间',
    UNIQUE KEY uk_msg_user (message_id, user_id),
    INDEX idx_message_id (message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息已读记录表';
