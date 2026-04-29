-- 知识图谱节点表
CREATE TABLE IF NOT EXISTS `zhinote_knowledge_graph_nodes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `note_id` int(11) DEFAULT NULL COMMENT '关联笔记ID，NULL表示全局聚合节点',
  `node_type` varchar(50) NOT NULL DEFAULT 'concept' COMMENT '节点类型：theme(主题)/chapter(章节)/concept(知识点)/exam_point(考点)',
  `content` varchar(500) NOT NULL COMMENT '节点内容/名称',
  `importance` varchar(20) DEFAULT '⭐' COMMENT '重要程度',
  `definition` text COMMENT '节点定义/描述',
  `is_user_created` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否用户手动创建：0-否，1-是',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_note_id` (`note_id`),
  KEY `idx_node_type` (`node_type`),
  KEY `idx_is_user_created` (`is_user_created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识图谱节点表';

-- 知识图谱边表（节点关系）
CREATE TABLE IF NOT EXISTS `zhinote_knowledge_graph_edges` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `note_id` int(11) DEFAULT NULL COMMENT '关联笔记ID，NULL表示全局聚合关系',
  `source_node_id` int(11) NOT NULL COMMENT '源节点ID',
  `target_node_id` int(11) NOT NULL COMMENT '目标节点ID',
  `relationship_type` varchar(100) DEFAULT '关联' COMMENT '关系类型：包含/依赖/前置/关联/因果等',
  `strength` int(11) DEFAULT 1 COMMENT '关系强度：1-弱 2-中 3-强',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_note_id` (`note_id`),
  KEY `idx_source_node` (`source_node_id`),
  KEY `idx_target_node` (`target_node_id`),
  CONSTRAINT `fk_edge_source` FOREIGN KEY (`source_node_id`) REFERENCES `zhinote_knowledge_graph_nodes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_edge_target` FOREIGN KEY (`target_node_id`) REFERENCES `zhinote_knowledge_graph_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识图谱边表（节点关系）';
