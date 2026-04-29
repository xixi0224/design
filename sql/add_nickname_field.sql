-- 为已存在的用户表添加 nickname 字段
ALTER TABLE zhinote_users 
ADD COLUMN IF NOT EXISTS nickname VARCHAR(50) DEFAULT '' AFTER username;
