-- 学习统计表
CREATE TABLE IF NOT EXISTS `zhinote_study_stats` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL COMMENT '用户ID',
  `study_date` date NOT NULL COMMENT '学习日期',
  `study_duration` int(11) DEFAULT 0 COMMENT '学习时长（分钟）',
  `review_count` int(11) DEFAULT 0 COMMENT '复习次数',
  `task_count` int(11) DEFAULT 0 COMMENT '完成任务数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_date` (`user_id`, `study_date`),
  KEY `idx_study_date` (`study_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习统计表';
