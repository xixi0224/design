-- ========================================
-- ZhiNote 数据库表字段修改脚本
-- 只修改字段，不删除表
-- ========================================

USE railway;

-- ========================================
-- 1. 修改 zhinote_notes 表（最重要！）
-- ========================================
-- 将 user_id 从 NOT NULL 改为允许 NULL

ALTER TABLE zhinote_notes 
MODIFY COLUMN user_id INT DEFAULT NULL COMMENT '用户ID，可为空';

-- ========================================
-- 2. 修改 zhinote_analysis 表
-- ========================================

-- 添加缺少的字段
ALTER TABLE zhinote_analysis 
ADD COLUMN doc_id INT NOT NULL COMMENT '关联文档/笔记ID' AFTER id;

ALTER TABLE zhinote_analysis 
ADD COLUMN section VARCHAR(255) COMMENT '段落/章节名' AFTER doc_id;

ALTER TABLE zhinote_analysis 
ADD COLUMN keywords TEXT COMMENT '关键词（JSON数组）' AFTER summary;

ALTER TABLE zhinote_analysis 
ADD COLUMN is_exam_point TINYINT(1) DEFAULT 0 COMMENT '是否考点' AFTER keywords;

ALTER TABLE zhinote_analysis 
ADD COLUMN importance VARCHAR(20) DEFAULT '⭐⭐' COMMENT '重要程度' AFTER is_exam_point;

-- 删除可能存在的错误字段（如果字段不存在会报错，忽略即可）
ALTER TABLE zhinote_analysis DROP COLUMN note_id;
ALTER TABLE zhinote_analysis DROP COLUMN key_points;
ALTER TABLE zhinote_analysis DROP COLUMN study_suggestions;

-- 添加索引
ALTER TABLE zhinote_analysis 
ADD INDEX idx_doc_id (doc_id);

-- ========================================
-- 3. 修改 zhinote_audio_records 表
-- ========================================

-- 添加正确的字段
ALTER TABLE zhinote_audio_records 
ADD COLUMN course_id INT DEFAULT 1 COMMENT '课程ID' AFTER id;

ALTER TABLE zhinote_audio_records 
ADD COLUMN filename VARCHAR(500) NOT NULL COMMENT '音频文件名' AFTER course_id;

ALTER TABLE zhinote_audio_records 
ADD COLUMN transcript_text TEXT COMMENT '语音转文本结果' AFTER status;

-- 删除错误的字段
ALTER TABLE zhinote_audio_records DROP COLUMN user_id;
ALTER TABLE zhinote_audio_records DROP COLUMN audio_path;
ALTER TABLE zhinote_audio_records DROP COLUMN transcript;

-- 添加索引
ALTER TABLE zhinote_audio_records 
ADD INDEX idx_course_id (course_id);

-- ========================================
-- 4. 修改 zhinote_auto_notes 表
-- ========================================

-- 添加缺失的字段
ALTER TABLE zhinote_auto_notes 
ADD COLUMN source_id INT NOT NULL COMMENT '源内容ID' AFTER id;

ALTER TABLE zhinote_auto_notes 
ADD COLUMN source_type VARCHAR(50) NOT NULL COMMENT '源类型：document/audio/text' AFTER source_id;

ALTER TABLE zhinote_auto_notes 
ADD COLUMN structure TEXT COMMENT '笔记结构（JSON）' AFTER content;

-- 添加索引
ALTER TABLE zhinote_auto_notes 
ADD INDEX idx_source (source_id, source_type);

-- ========================================
-- 5. 修改 zhinote_reminders 表
-- ========================================

-- 添加 updated_at 字段
ALTER TABLE zhinote_reminders 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- 添加索引
ALTER TABLE zhinote_reminders 
ADD INDEX idx_user_id (user_id);

ALTER TABLE zhinote_reminders 
ADD INDEX idx_reminder_time (reminder_time);

-- ========================================
-- 6. 修改 zhinote_notes 表索引
-- ========================================

ALTER TABLE zhinote_notes 
ADD INDEX idx_user_id (user_id);

ALTER TABLE zhinote_notes 
ADD INDEX idx_created_at (created_at);

-- ========================================
-- 7. 重命名表（如果存在）
-- ========================================

-- 如果存在 zhinote_categories，重命名为 zhinote_knowledge_categories
RENAME TABLE zhinote_categories TO zhinote_knowledge_categories;

-- ========================================
-- 完成
-- ========================================
SELECT '✅ 数据库表字段修改完成！' AS message;
SELECT '现在可以测试小程序了' AS note;
