from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.upload import router as upload_router
from app.routers.analysis import router as analysis_router
from app.routers.notes import router as notes_router
from app.routers.visualization import router as visualization_router
from app.routers.animation import router as animation_router
from app.routers.content_input import router as content_input_router
from app.routers.ai_analysis import router as ai_analysis_router
from app.routers.ai import router as ai_router
from app.routers.knowledge_structure import router as knowledge_structure_router
from app.routers.study_analysis import router as study_analysis_router
from app.routers.study_assist import router as study_assist_router
from app.routers.learning_plan import router as learning_plan_router
from app.routers.study_stats import router as study_stats_router
from app.routers.report import router as report_router
from app.routers.auth import router as auth_router

app = FastAPI(title="ZhiNote Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(visualization_router, prefix="/api")
app.include_router(animation_router, prefix="/api")
app.include_router(content_input_router, prefix="/api")
app.include_router(ai_analysis_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(knowledge_structure_router, prefix="/api")
app.include_router(study_analysis_router, prefix="/api")
app.include_router(study_assist_router, prefix="/api")
# 学习计划路由
app.include_router(learning_plan_router, prefix="/api")

# 学习统计路由
app.include_router(study_stats_router, prefix="/api")

# 学习报告路由
app.include_router(report_router, prefix="/api")

# 认证路由
app.include_router(auth_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "ZhiNote backend is running"}