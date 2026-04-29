-- ========================================
-- ZhiNote 完整数据库表结构（重新建表版）
-- 用于 Railway MySQL 数据库
-- 使用方法：先删除旧表，再创建新表
-- ========================================

USE railway;

-- 禁用外键检查（避免删除顺序问题）
SET FOREIGN_KEY_CHECKS = 0;

-- ========================================
-- 删除所有旧表（按依赖关系倒序）
-- ========================================
DROP TABLE IF EXISTS zhinote_schools;
DROP TABLE IF EXISTS zhinote_export_records;
DROP TABLE IF EXISTS zhinote_reminders;
DROP TABLE IF EXISTS zhinote_learning_plans;
DROP TABLE IF EXISTS zhinote_study_records;
DROP TABLE IF EXISTS zhinote_study_stats;
DROP TABLE IF EXISTS zhinote_knowledge_categories;
DROP TABLE IF EXISTS zhinote_knowledge_points;
DROP TABLE IF EXISTS zhinote_knowledge_graph_edges;
DROP TABLE IF EXISTS zhinote_knowledge_graph_nodes;
DROP TABLE IF EXISTS zhinote_auto_notes;
DROP TABLE IF EXISTS zhinote_text_inputs;
DROP TABLE IF EXISTS zhinote_audio_records;
DROP TABLE IF EXISTS zhinote_documents;
DROP TABLE IF EXISTS zhinote_analysis;
DROP TABLE IF EXISTS zhinote_notes;
DROP TABLE IF EXISTS zhinote_password_reset_tokens;
DROP TABLE IF EXISTS zhinote_users;

-- 启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ========================================
-- 1. 用户认证模块
-- ========================================

-- 用户表
CREATE TABLE zhinote_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    nickname VARCHAR(50) DEFAULT '',
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1,
    last_login TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 密码重置令牌表
CREATE TABLE zhinote_password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(100) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES zhinote_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='密码重置令牌表';

-- ========================================
-- 2. 笔记管理模块
-- ========================================

-- 笔记表
CREATE TABLE zhinote_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL COMMENT '用户ID，可为空',
    title VARCHAR(255) NOT NULL,
    content TEXT,
    note_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='笔记表';

-- AI分析结果表
CREATE TABLE zhinote_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_id INT NOT NULL COMMENT '关联文档/笔记ID',
    section VARCHAR(255) COMMENT '段落/章节名',
    summary TEXT COMMENT '内容摘要',
    keywords TEXT COMMENT '关键词（JSON数组）',
    is_exam_point TINYINT(1) DEFAULT 0 COMMENT '是否考点',
    importance VARCHAR(20) DEFAULT '⭐⭐' COMMENT '重要程度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_doc_id (doc_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI分析结果表';

-- ========================================
-- 3. 内容输入模块
-- ========================================

-- 文档表（PDF/DOCX）
CREATE TABLE zhinote_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    file_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档表';

-- 音频记录表
CREATE TABLE zhinote_audio_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT DEFAULT 1 COMMENT '课程ID',
    filename VARCHAR(500) NOT NULL COMMENT '音频文件名',
    duration INT COMMENT '时长（秒）',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed',
    transcript_text TEXT COMMENT '语音转文本结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_course_id (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='音频记录表';

-- 文本输入表
CREATE TABLE zhinote_text_inputs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文本输入表';

-- 自动笔记表
CREATE TABLE zhinote_auto_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_id INT NOT NULL COMMENT '源内容ID',
    source_type VARCHAR(50) NOT NULL COMMENT '源类型：document/audio/text',
    title VARCHAR(255) NOT NULL,
    content TEXT,
    structure TEXT COMMENT '笔记结构（JSON）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_source (source_id, source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='自动笔记表';

-- ========================================
-- 4. 知识图谱模块
-- ========================================

-- 知识图谱节点表
CREATE TABLE zhinote_knowledge_graph_nodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT DEFAULT NULL COMMENT '关联笔记ID，NULL表示全局聚合节点',
    node_type VARCHAR(50) NOT NULL DEFAULT 'concept' COMMENT '节点类型：theme/chapter/concept/exam_point',
    content VARCHAR(500) NOT NULL COMMENT '节点内容/名称',
    importance VARCHAR(20) DEFAULT '⭐' COMMENT '重要程度',
    definition TEXT COMMENT '节点定义/描述',
    is_user_created TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否用户手动创建',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_note_id (note_id),
    INDEX idx_node_type (node_type),
    INDEX idx_is_user_created (is_user_created)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识图谱节点表';

-- 知识图谱边表（节点关系）
CREATE TABLE zhinote_knowledge_graph_edges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT DEFAULT NULL COMMENT '关联笔记ID，NULL表示全局聚合关系',
    source_node_id INT NOT NULL COMMENT '源节点ID',
    target_node_id INT NOT NULL COMMENT '目标节点ID',
    relationship_type VARCHAR(100) DEFAULT '关联' COMMENT '关系类型',
    strength INT DEFAULT 1 COMMENT '关系强度：1-弱 2-中 3-强',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_note_id (note_id),
    INDEX idx_source_node (source_node_id),
    INDEX idx_target_node (target_node_id),
    CONSTRAINT fk_edge_source FOREIGN KEY (source_node_id) REFERENCES zhinote_knowledge_graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_edge_target FOREIGN KEY (target_node_id) REFERENCES zhinote_knowledge_graph_nodes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识图谱边表';

-- 知识点表
CREATE TABLE zhinote_knowledge_points (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    content TEXT NOT NULL,
    importance VARCHAR(50),
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_note_id (note_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点表';

-- 知识分类表
CREATE TABLE zhinote_knowledge_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识分类表';

-- ========================================
-- 5. 学习分析模块
-- ========================================

-- 学习统计表
CREATE TABLE zhinote_study_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL COMMENT '用户ID',
    study_date DATE NOT NULL COMMENT '学习日期',
    study_duration INT DEFAULT 0 COMMENT '学习时长（分钟）',
    review_count INT DEFAULT 0 COMMENT '复习次数',
    task_count INT DEFAULT 0 COMMENT '完成任务数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY idx_user_date (user_id, study_date),
    INDEX idx_study_date (study_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习统计表';

-- 学习记录表
CREATE TABLE zhinote_study_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    note_id INT,
    duration INT NOT NULL COMMENT '学习时长（分钟）',
    date DATE NOT NULL COMMENT '学习日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习记录表';

-- 学习计划表
CREATE TABLE zhinote_learning_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exam_date DATE NOT NULL COMMENT '考试日期',
    daily_hours DECIMAL(3,1) NOT NULL COMMENT '每日可用时间（小时）',
    pending_tasks TEXT COMMENT '待完成任务',
    exam_subject VARCHAR(100) NOT NULL COMMENT '考试科目',
    plan_data LONGTEXT COMMENT '计划数据（JSON格式）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习计划表';

-- ========================================
-- 6. 学习辅助模块
-- ========================================

-- 复习提醒表
CREATE TABLE zhinote_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT,
    reminder_time DATETIME NOT NULL COMMENT '提醒时间',
    is_completed TINYINT(1) DEFAULT 0 COMMENT '是否完成',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_reminder_time (reminder_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复习提醒表';

-- 导出记录表
CREATE TABLE zhinote_export_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    note_id INT NOT NULL,
    export_type VARCHAR(50) COMMENT '导出类型：pdf/docx/markdown',
    export_path VARCHAR(500) COMMENT '导出文件路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_note_id (note_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='导出记录表';

-- 学校推荐表
CREATE TABLE zhinote_schools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '学校名称',
    location VARCHAR(255) COMMENT '学校位置',
    ranking VARCHAR(50) COMMENT '排名',
    type VARCHAR(50) COMMENT '学校类型',
    min_score INT COMMENT '最低分数线',
    majors TEXT COMMENT '专业列表',
    description TEXT COMMENT '学校描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学校推荐表';

-- ========================================
-- 验证表创建结果
-- ========================================
SELECT '========================================' AS '';
SELECT '✅ 所有表创建成功！' AS message;
SELECT '========================================' AS '';
SELECT CONCAT('共创建 ', COUNT(*), ' 个表') AS summary 
FROM information_schema.tables 
WHERE table_schema = 'railway' AND table_name LIKE 'zhinote_%';
SELECT '========================================' AS '';
