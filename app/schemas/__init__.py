from app.schemas.content_input import (
    AudioRecordCreate,
    AudioRecordResponse,
    TextInputCreate,
    TextInputResponse,
)

from app.schemas.ai_analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ASRRequest,
    ASRResponse,
    SummaryResponse,
    ExamPointResponse,
)

from app.schemas.knowledge_structure import (
    AutoNoteCreate,
    AutoNoteResponse,
    KnowledgePointCreate,
    KnowledgePointResponse,
)

from app.schemas.study_analysis import (
    StudyRecordCreate,
    StudyRecordResponse,
    ExamPointHeatResponse,
)

from app.schemas.study_assist import (
    ExportRequest,
    ExportResponse,
)