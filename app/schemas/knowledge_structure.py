from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

class AutoNoteCreate(BaseModel):
    source_id: int
    source_type: str

class AutoNoteResponse(BaseModel):
    id: int
    source_id: int
    source_type: str
    title: str
    content: str
    structure: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgePointCreate(BaseModel):
    note_id: int
    content: str
    importance: str
    category_id: int

class KnowledgePointResponse(BaseModel):
    id: int
    note_id: int
    content: str
    importance: str
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class KnowledgeCategoryCreate(BaseModel):
    name: str
    description: str

class KnowledgeCategoryResponse(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True

class KnowledgeGraphNode(BaseModel):
    id: int
    note_id: int
    node_type: str
    content: str
    importance: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeGraphEdge(BaseModel):
    id: int
    note_id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str
    strength: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]