import json
import dashscope
from dashscope import Generation
from datetime import datetime
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
from app.db import get_conn
from app.schemas.knowledge_structure import AutoNoteCreate, AutoNoteResponse, KnowledgePointResponse

dashscope.api_key = DASHSCOPE_API_KEY

def get_source_content(source_id: int, source_type: str):
    conn = get_conn()
    cursor = conn.cursor()

    if source_type == "document":
        cursor.execute("SELECT content, filename FROM zhinote_documents WHERE id = %s", (source_id,))
    elif source_type == "audio":
        cursor.execute("SELECT filename FROM zhinote_audio_records WHERE id = %s", (source_id,))
    elif source_type == "text":
        cursor.execute("SELECT content, title FROM zhinote_text_inputs WHERE id = %s", (source_id,))
    else:
        raise ValueError("Invalid source type")

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        raise ValueError("Source not found")

    return result

def generate_auto_note(request: AutoNoteCreate):
    source_result = get_source_content(request.source_id, request.source_type)

    if request.source_type == "document":
        content, title = source_result[0], source_result[1]
    elif request.source_type == "audio":
        title = source_result[0]
        content = f"[音频文件]: {source_result[0]}"
    elif request.source_type == "text":
        content, title = source_result[0], source_result[1]
    else:
        raise ValueError("Invalid source type")

    note_content, structure = generate_note_from_content(content, title)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_auto_notes (source_id, source_type, title, content, structure)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (request.source_id, request.source_type, title, note_content, json.dumps(structure, ensure_ascii=False))
    )
    note_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return AutoNoteResponse(
        id=note_id,
        source_id=request.source_id,
        source_type=request.source_type,
        title=title,
        content=note_content,
        structure=structure,
        created_at=datetime.now()
    )

def generate_note_from_content(content: str, title: str):
    prompt = f"""
你是一个智能笔记生成助手。请根据以下内容生成结构化的学习笔记。

要求：
1. 生成笔记标题
2. 将内容组织成多个章节
3. 每个章节包含：小节标题、内容摘要、关键知识点
4. 只输出JSON格式：
{{
    "title": "笔记标题",
    "sections": [
        {{
            "title": "章节1",
            "summary": "章节摘要",
            "key_points": ["要点1", "要点2"]
        }}
    ]
}}

内容：
{content[:12000]}
"""

    response = Generation.call(
        model=DASHSCOPE_MODEL,
        messages=[
            {"role": "system", "content": "你是一个严谨的教育AI助手，只输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message",
        response_format={"type": "json_object"}
    )

    result = json.loads(response.output.choices[0].message.content)
    note_content = json.dumps(result, ensure_ascii=False, indent=2)

    return note_content, result

def get_knowledge_points(note_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, note_id, content, importance, category_id, created_at FROM zhinote_knowledge_points WHERE note_id = %s",
        (note_id,)
    )
    points = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        KnowledgePointResponse(
            id=point[0],
            note_id=point[1],
            content=point[2],
            importance=point[3],
            category_id=point[4],
            created_at=point[5]
        )
        for point in points
    ]

def create_knowledge_point(note_id: int, content: str, importance: str, category_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_knowledge_points (note_id, content, importance, category_id)
        VALUES (%s, %s, %s, %s)
        """,
        (note_id, content, importance, category_id)
    )
    point_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return KnowledgePointResponse(
        id=point_id,
        note_id=note_id,
        content=content,
        importance=importance,
        category_id=category_id,
        created_at=datetime.now()
    )

def get_categories():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM zhinote_knowledge_categories")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {"id": cat[0], "name": cat[1], "description": cat[2]}
        for cat in categories
    ]

def create_knowledge_category(name: str, description: str):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_knowledge_categories (name, description)
        VALUES (%s, %s)
        """,
        (name, description)
    )
    category_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    from app.schemas.knowledge_structure import KnowledgeCategoryResponse
    return KnowledgeCategoryResponse(
        id=category_id,
        name=name,
        description=description
    )

def generate_knowledge_graph(note_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    
    # 获取笔记内容：先在 zhinote_notes 查找，找不到再去 zhinote_auto_notes
    cursor.execute("SELECT content, title FROM zhinote_notes WHERE id = %s", (note_id,))
    note_result = cursor.fetchone()
    if not note_result:
        cursor.execute("SELECT content, title FROM zhinote_auto_notes WHERE id = %s", (note_id,))
        note_result = cursor.fetchone()
    if not note_result:
        cursor.close()
        conn.close()
        raise ValueError("Note not found")
    
    note_content, note_title = note_result[0], note_result[1] if len(note_result) > 1 else ""
    
    # 生成知识图谱节点和关系
    # 这里使用AI生成知识点之间的关联
    import dashscope
    from dashscope import Generation
    import json
    
    prompt = f"""
    你是一个知识图谱生成助手。请根据以下笔记内容，提取知识点并生成它们之间的关联关系。
    
    要求：
    1. 提取出主要的知识点作为节点
    2. 分析知识点之间的关系作为边
    3. 为每个节点分配重要性等级（⭐、⭐⭐、⭐⭐⭐）
    4. 为每条边指定关系类型（如：包含、依赖、因果、并列等）
    5. 只输出JSON格式：
    {{
        "nodes": [
            {{
                "content": "知识点内容",
                "importance": "⭐",
                "type": "概念/原理/方法/其他"
            }}
        ],
        "edges": [
            {{
                "source": "源知识点内容",
                "target": "目标知识点内容",
                "relationship": "关系类型",
                "strength": 1
            }}
        ]
    }}
    
    笔记内容：
    {note_content[:5000]}
    """
    
    response = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个严谨的教育AI助手，只输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message",
        response_format={"type": "json_object"}
    )
    
    graph_data = json.loads(response.output.choices[0].message.content)
    
    # 清除现有图谱数据
    cursor.execute("DELETE FROM zhinote_knowledge_graph_edges WHERE note_id = %s", (note_id,))
    cursor.execute("DELETE FROM zhinote_knowledge_graph_nodes WHERE note_id = %s", (note_id,))
    
    # 插入节点
    node_mapping = {}
    for node in graph_data.get("nodes", []):
        cursor.execute(
            """
            INSERT INTO zhinote_knowledge_graph_nodes (note_id, node_type, content, importance)
            VALUES (%s, %s, %s, %s)
            """,
            (note_id, node.get("type", "概念"), node.get("content"), node.get("importance", "⭐"))
        )
        node_id = cursor.lastrowid
        node_mapping[node.get("content")] = node_id
    
    # 插入边
    for edge in graph_data.get("edges", []):
        source_id = node_mapping.get(edge.get("source"))
        target_id = node_mapping.get(edge.get("target"))
        if source_id and target_id:
            cursor.execute(
                """
                INSERT INTO zhinote_knowledge_graph_edges (note_id, source_node_id, target_node_id, relationship_type, strength)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (note_id, source_id, target_id, edge.get("relationship"), edge.get("strength", 1))
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "message": "知识图谱生成成功"}

def get_knowledge_graph(note_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    
    # 获取节点
    cursor.execute(
        """
        SELECT id, note_id, node_type, content, importance, created_at, updated_at
        FROM zhinote_knowledge_graph_nodes
        WHERE note_id = %s
        """,
        (note_id,)
    )
    nodes = cursor.fetchall()
    
    # 获取边
    cursor.execute(
        """
        SELECT id, note_id, source_node_id, target_node_id, relationship_type, strength, created_at, updated_at
        FROM zhinote_knowledge_graph_edges
        WHERE note_id = %s
        """,
        (note_id,)
    )
    edges = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    from app.schemas.knowledge_structure import KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphResponse
    
    node_list = [
        KnowledgeGraphNode(
            id=node[0],
            note_id=node[1],
            node_type=node[2],
            content=node[3],
            importance=node[4],
            created_at=node[5],
            updated_at=node[6]
        )
        for node in nodes
    ]
    
    edge_list = [
        KnowledgeGraphEdge(
            id=edge[0],
            note_id=edge[1],
            source_node_id=edge[2],
            target_node_id=edge[3],
            relationship_type=edge[4],
            strength=edge[5],
            created_at=edge[6],
            updated_at=edge[7]
        )
        for edge in edges
    ]
    
    return KnowledgeGraphResponse(nodes=node_list, edges=edge_list)

def generate_global_knowledge_graph():
    """
    基于所有笔记生成全局知识图谱
    读取zhinote_notes和zhinote_analysis的数据，调用AI生成全局图谱
    """
    conn = get_conn()
    cursor = conn.cursor()
    
    # 读取所有笔记（限制最近20条，避免prompt过长）
    cursor.execute(
        """
        SELECT id, title, content, created_at
        FROM zhinote_notes
        ORDER BY created_at DESC
        LIMIT 20
        """
    )
    notes = cursor.fetchall()
    
    if not notes:
        cursor.close()
        conn.close()
        return {"success": False, "message": "暂无笔记，无法生成知识图谱"}
    
    # 构建笔记内容摘要
    notes_summary = []
    for note_id, title, content, created_at in notes:
        # 获取该笔记的分析数据
        cursor.execute(
            """
            SELECT section, summary, keywords, is_exam_point, importance
            FROM zhinote_analysis
            WHERE doc_id = %s
            ORDER BY id ASC
            """,
            (note_id,)
        )
        analysis_rows = cursor.fetchall()
        
        note_sections = []
        for section, summary, keywords, is_exam_point, importance in analysis_rows:
            note_sections.append({
                "section": section,
                "summary": summary,
                "keywords": keywords,
                "is_exam_point": bool(is_exam_point),
                "importance": importance
            })
        
        notes_summary.append({
            "id": note_id,
            "title": title,
            "content_preview": str(content)[:300] if content else "",
            "sections": note_sections
        })
    
    # 构建AI Prompt
    prompt = f"""你是一个专业的教育知识图谱构建专家。请根据以下用户笔记内容，构建一张完整的全局知识图谱。

要求：
1. 提取所有笔记中的核心主题作为中心节点（node_type="theme"）
2. 提取章节/大模块作为二级节点（node_type="chapter"）
3. 提取细分知识点作为三级节点（node_type="concept"）
4. 提取高频考点作为特殊节点（node_type="exam_point"），必须高亮显示
5. 分析节点之间的关系作为边（包含、依赖、前置、关联、因果等）
6. 每个节点必须包含：name（名称）、type（类型）、definition（定义，50字以内）、importance（重要程度：1-5数字）
7. 每条边必须包含：source（源节点名称）、target（目标节点名称）、relation（关系类型）
8. 只输出标准JSON格式，不要包含任何其他文字：

{{
  "nodes": [
    {{"name": "节点名称", "type": "theme/chapter/concept/exam_point", "definition": "定义描述", "importance": 5}}
  ],
  "links": [
    {{"source": "源节点名称", "target": "目标节点名称", "relation": "关系类型"}}
  ]
}}

用户笔记数据：
{json.dumps(notes_summary, ensure_ascii=False, indent=2)[:8000]}
"""
    
    # 调用AI生成图谱
    response = Generation.call(
        model=DASHSCOPE_MODEL,
        messages=[
            {"role": "system", "content": "你是一个严谨的教育知识图谱构建专家，只输出标准JSON格式。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message",
        response_format={"type": "json_object"}
    )
    
    graph_data_text = response.output.choices[0].message.content
    
    # 解析JSON
    import re
    json_match = re.search(r'\{.*\}', graph_data_text, re.DOTALL)
    if json_match:
        graph_data = json.loads(json_match.group())
    else:
        graph_data = json.loads(graph_data_text.strip())
    
    # 清空旧的全局图谱数据（note_id IS NULL）
    cursor.execute(
        """
        DELETE e FROM zhinote_knowledge_graph_edges e
        INNER JOIN zhinote_knowledge_graph_nodes n ON e.source_node_id = n.id
        WHERE n.note_id IS NULL
        """
    )
    cursor.execute("DELETE FROM zhinote_knowledge_graph_nodes WHERE note_id IS NULL")
    
    # 插入新节点
    node_mapping = {}
    for node in graph_data.get("nodes", []):
        node_type = node.get("type", "concept")
        # 标准化类型
        if node_type not in ["theme", "chapter", "concept", "exam_point"]:
            node_type = "concept"
        
        importance = node.get("importance", 1)
        if isinstance(importance, int):
            importance = "⭐" * importance if importance <= 3 else "⭐⭐⭐"
        elif not importance:
            importance = "⭐"
        
        cursor.execute(
            """
            INSERT INTO zhinote_knowledge_graph_nodes 
            (note_id, node_type, content, importance, definition, is_user_created)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (None, node_type, node.get("name", ""), importance, 
             node.get("definition", ""), 0)
        )
        node_id = cursor.lastrowid
        node_mapping[node.get("name", "")] = node_id
    
    # 插入边
    for link in graph_data.get("links", []):
        source_id = node_mapping.get(link.get("source"))
        target_id = node_mapping.get(link.get("target"))
        if source_id and target_id:
            cursor.execute(
                """
                INSERT INTO zhinote_knowledge_graph_edges 
                (note_id, source_node_id, target_node_id, relationship_type, strength)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (None, source_id, target_id, link.get("relation", "关联"), 2)
            )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    node_count = len(graph_data.get("nodes", []))
    edge_count = len(graph_data.get("links", []))
    
    return {
        "success": True, 
        "message": f"全局知识图谱生成成功，共{node_count}个节点，{edge_count}条关系",
        "nodeCount": node_count,
        "edgeCount": edge_count
    }

def get_global_knowledge_graph():
    """查询全局知识图谱（note_id IS NULL的节点和边）"""
    conn = get_conn()
    cursor = conn.cursor()
    
    # 获取全局节点
    cursor.execute(
        """
        SELECT id, note_id, node_type, content, importance, definition, is_user_created, created_at
        FROM zhinote_knowledge_graph_nodes
        WHERE note_id IS NULL
        ORDER BY 
            FIELD(node_type, 'theme', 'chapter', 'concept', 'exam_point'),
            importance DESC
        """
    )
    nodes = cursor.fetchall()
    
    # 获取全局边
    cursor.execute(
        """
        SELECT e.id, e.note_id, e.source_node_id, e.target_node_id, e.relationship_type, e.strength,
               n1.content as source_name, n2.content as target_name
        FROM zhinote_knowledge_graph_edges e
        INNER JOIN zhinote_knowledge_graph_nodes n1 ON e.source_node_id = n1.id
        INNER JOIN zhinote_knowledge_graph_nodes n2 ON e.target_node_id = n2.id
        WHERE e.note_id IS NULL AND n1.note_id IS NULL AND n2.note_id IS NULL
        """
    )
    edges = cursor.fetchall()
    
    # 构建ECharts需要的格式
    node_list = []
    node_id_map = {}
    for idx, node in enumerate(nodes):
        node_id, note_id, node_type, content, importance, definition, is_user_created, created_at = node
        node_id_map[node_id] = idx
        
        # 根据类型和重要性设置节点大小
        symbol_size = 40
        if node_type == "theme":
            symbol_size = 70
        elif node_type == "chapter":
            symbol_size = 55
        elif node_type == "exam_point":
            symbol_size = 50
        elif importance and "⭐⭐⭐" in str(importance):
            symbol_size = 50
        elif importance and "⭐⭐" in str(importance):
            symbol_size = 45
        
        node_list.append({
            "id": str(node_id),
            "name": content,
            "value": symbol_size,
            "symbolSize": symbol_size,
            "category": node_type,
            "draggable": True,
            "definition": definition or "",
            "importance": importance or "⭐",
            "isUserCreated": bool(is_user_created)
        })
    
    link_list = []
    for edge in edges:
        edge_id, note_id, source_node_id, target_node_id, relationship_type, strength, source_name, target_name = edge
        link_list.append({
            "source": str(source_node_id),
            "target": str(target_node_id),
            "value": relationship_type,
            "name": relationship_type
        })
    
    # 构建categories（用于ECharts图例）
    categories = [
        {"name": "theme"},
        {"name": "chapter"},
        {"name": "concept"},
        {"name": "exam_point"}
    ]
    
    cursor.close()
    conn.close()
    
    return {
        "nodes": node_list,
        "links": link_list,
        "categories": categories,
        "nodeCount": len(node_list),
        "edgeCount": len(link_list)
    }

def get_node_related_notes(node_content: str):
    """根据节点内容反查关联笔记"""
    conn = get_conn()
    cursor = conn.cursor()
    
    # 模糊匹配：查找analysis表中包含该知识点的笔记
    cursor.execute(
        """
        SELECT DISTINCT n.id, n.title, n.created_at
        FROM zhinote_notes n
        INNER JOIN zhinote_analysis a ON n.id = a.doc_id
        WHERE a.section LIKE %s OR a.summary LIKE %s OR a.keywords LIKE %s
        ORDER BY n.created_at DESC
        LIMIT 5
        """,
        (f"%{node_content}%", f"%{node_content}%", f"%{node_content}%")
    )
    notes = cursor.fetchall()
    
    note_list = []
    for note_id, title, created_at in notes:
        note_list.append({
            "id": note_id,
            "title": title,
            "date": created_at.strftime("%Y-%m-%d") if hasattr(created_at, 'strftime') else str(created_at)[:10]
        })
    
    cursor.close()
    conn.close()
    
    return note_list

def create_graph_node(content: str, node_type: str, definition: str = "", importance: str = "⭐"):
    """用户手动创建节点"""
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO zhinote_knowledge_graph_nodes 
        (note_id, node_type, content, importance, definition, is_user_created)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (None, node_type, content, importance, definition, 1)
    )
    node_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": node_id, "content": content, "node_type": node_type}

def create_graph_edge(source_node_id: int, target_node_id: int, relationship_type: str, strength: int = 2):
    """用户手动创建关系"""
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO zhinote_knowledge_graph_edges 
        (note_id, source_node_id, target_node_id, relationship_type, strength)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (None, source_node_id, target_node_id, relationship_type, strength)
    )
    edge_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"id": edge_id, "source": source_node_id, "target": target_node_id}

def delete_graph_node(node_id: int):
    """删除节点（仅允许删除用户创建的节点）"""
    conn = get_conn()
    cursor = conn.cursor()
    
    # 先检查是否是用户创建的
    cursor.execute(
        "SELECT is_user_created FROM zhinote_knowledge_graph_nodes WHERE id = %s",
        (node_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        conn.close()
        return {"success": False, "message": "节点不存在"}
    
    if not result[0]:
        cursor.close()
        conn.close()
        return {"success": False, "message": "只能删除用户手动创建的节点"}
    
    # 外键会自动删除关联的边
    cursor.execute("DELETE FROM zhinote_knowledge_graph_nodes WHERE id = %s", (node_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "message": "节点删除成功"}

def delete_graph_edge(edge_id: int):
    """删除关系"""
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM zhinote_knowledge_graph_edges WHERE id = %s", (edge_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"success": True, "message": "关系删除成功"}