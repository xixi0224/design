from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.schemas.knowledge_structure import AutoNoteCreate, AutoNoteResponse, KnowledgePointResponse, KnowledgeCategoryCreate, KnowledgeCategoryResponse, KnowledgeGraphResponse
from app.services.knowledge_service import (
    generate_auto_note, get_knowledge_points, create_knowledge_point, 
    get_categories, create_knowledge_category, generate_knowledge_graph, get_knowledge_graph,
    generate_global_knowledge_graph, get_global_knowledge_graph, get_node_related_notes,
    create_graph_node, create_graph_edge, delete_graph_node, delete_graph_edge
)

router = APIRouter(tags=["knowledge_structure"])

@router.post("/auto-note", response_model=AutoNoteResponse)
async def generate_auto_note_endpoint(request: AutoNoteCreate):
    try:
        return generate_auto_note(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动笔记生成失败: {str(e)}")

@router.get("/knowledge-points/{note_id}", response_model=list[KnowledgePointResponse])
async def get_knowledge_points_endpoint(note_id: int):
    try:
        return get_knowledge_points(note_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识点失败: {str(e)}")

@router.post("/knowledge-points", response_model=KnowledgePointResponse)
async def create_knowledge_point_endpoint(
    note_id: int,
    content: str,
    importance: str = "⭐",
    category_id: int = 1
):
    try:
        return create_knowledge_point(note_id, content, importance, category_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识点失败: {str(e)}")

@router.get("/categories", response_model=list[KnowledgeCategoryResponse])
async def get_categories_endpoint():
    try:
        categories = get_categories()
        return [
            KnowledgeCategoryResponse(
                id=cat["id"],
                name=cat["name"],
                description=cat["description"]
            )
            for cat in categories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")

@router.post("/categories", response_model=KnowledgeCategoryResponse)
async def create_category_endpoint(category: KnowledgeCategoryCreate):
    try:
        return create_knowledge_category(category.name, category.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

@router.post("/knowledge-graph/generate/{note_id}")
async def generate_knowledge_graph_endpoint(note_id: int):
    try:
        return generate_knowledge_graph(note_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成知识图谱失败: {str(e)}")

@router.get("/knowledge-graph/{note_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph_endpoint(note_id: int):
    try:
        return get_knowledge_graph(note_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识图谱失败: {str(e)}")

@router.get("/global-knowledge-graph")
async def get_global_knowledge_graph_endpoint():
    """获取全局知识图谱"""
    try:
        result = get_global_knowledge_graph()
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全局知识图谱失败: {str(e)}")

@router.post("/global-knowledge-graph/generate")
async def generate_global_knowledge_graph_endpoint():
    """触发重新生成全局知识图谱"""
    try:
        result = generate_global_knowledge_graph()
        return {"code": 0, "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成全局知识图谱失败: {str(e)}")

@router.get("/knowledge-graph/node/{node_id}/notes")
async def get_node_related_notes_endpoint(node_id: int):
    """获取节点关联的笔记"""
    try:
        conn = __import__('app.services.knowledge_service', fromlist=['get_conn']).get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM zhinote_knowledge_graph_nodes WHERE id = %s",
            (node_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        notes = get_node_related_notes(result[0])
        return {"code": 0, "data": {"notes": notes}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关联笔记失败: {str(e)}")

@router.post("/knowledge-graph/node")
async def create_graph_node_endpoint(data: Dict[str, Any] = Body(...)):
    """用户手动创建节点"""
    try:
        content = data.get("content") or data.get("name")
        node_type = data.get("nodeType") or data.get("node_type", "concept")
        definition = data.get("definition", "")
        importance = data.get("importance", "⭐")
        
        if not content:
            raise HTTPException(status_code=400, detail="节点内容不能为空")
        
        result = create_graph_node(content, node_type, definition, importance)
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建节点失败: {str(e)}")

@router.post("/knowledge-graph/edge")
async def create_graph_edge_endpoint(data: Dict[str, Any] = Body(...)):
    """用户手动创建关系"""
    try:
        source_id = data.get("sourceNodeId")
        target_id = data.get("targetNodeId")
        relationship_type = data.get("relationshipType", "关联")
        strength = data.get("strength", 2)
        
        if not source_id or not target_id:
            raise HTTPException(status_code=400, detail="源节点和目标节点不能为空")
        
        result = create_graph_edge(source_id, target_id, relationship_type, strength)
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")

@router.delete("/knowledge-graph/node/{node_id}")
async def delete_graph_node_endpoint(node_id: int):
    """删除节点（仅用户创建的）"""
    try:
        result = delete_graph_node(node_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return {"code": 0, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除节点失败: {str(e)}")

@router.delete("/knowledge-graph/edge/{edge_id}")
async def delete_graph_edge_endpoint(edge_id: int):
    """删除关系"""
    try:
        result = delete_graph_edge(edge_id)
        return {"code": 0, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除关系失败: {str(e)}")