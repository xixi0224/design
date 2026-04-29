# ZhiNote 前后端集成文档

## 1. 项目概述

ZhiNote 是一个基于 AI 的智能学习笔记应用，提供语音识别、AI 分析、知识结构化等功能。本文档详细说明后端 API 接口和前端集成方案。

## 2. 后端技术栈

- **框架**: FastAPI
- **数据库**: MySQL
- **AI 服务**: 阿里云 DashScope、百度云 ASR
- **文件处理**: FFmpeg (音频处理)
- **部署**: 本地开发服务器 / 云服务器

## 3. 后端服务信息

### 3.1 本地开发环境
- **服务地址**: `http://127.0.0.1:8000`
- **API 文档**: `http://127.0.0.1:8000/docs` (Swagger UI)
- **健康检查**: `http://127.0.0.1:8000/`

### 3.2 生产环境配置
- **环境变量**: 需要配置以下环境变量
  - `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥
  - `MYSQL_HOST`: MySQL 主机地址
  - `MYSQL_USER`: MySQL 用户名
  - `MYSQL_PASSWORD`: MySQL 密码
  - `MYSQL_DATABASE`: 数据库名

## 4. 数据库结构

### 4.1 核心数据表

| 表名 | 功能 |
|------|------|
| `zhinote_documents` | 文档表（PDF/DOCX） |
| `zhinote_audio_records` | 音频记录表 |
| `zhinote_text_inputs` | 文本输入表 |
| `zhinote_ai_analysis` | AI 分析结果表 |
| `zhinote_notes` | 笔记表 |
| `zhinote_knowledge_points` | 知识点表 |
| `zhinote_categories` | 知识分类表 |
| `zhinote_study_records` | 学习记录表 |
| `zhinote_reminders` | 复习提醒表 |
| `zhinote_export_records` | 导出记录表 |

### 4.2 数据库初始化
确保 MySQL 服务运行，并创建对应的数据库和表结构。

## 5. API 接口文档

### 5.1 内容输入模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/upload/audio` | POST | 上传音频文件 | `file: UploadFile`<br>`course_id: int` | `{"audio_id": int, "filename": str, "duration": float, "status": str}` |
| `/api/text-input` | POST | 文本输入 | `{"content": str, "course_id": int, "user_id": int, "tags": [str]}` | `{"id": int, "content": str, "created_at": datetime}` |

### 5.2 文件上传模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/upload` | POST | 上传 PDF/DOCX | `file: UploadFile`<br>`course_id: int` | `{"message": str, "doc_id": int, "filename": str, "text_length": int}` |

### 5.3 AI 分析模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/analyze` | POST | AI 分析 | `{"source_id": int, "source_type": str, "analysis_type": str}` | `{"id": int, "source_id": int, "source_type": str, "analysis_type": str, "result": object, "created_at": datetime}` |
| `/api/asr` | POST | 语音转文本 | `{"audio_id": int}` | `{"audio_id": int, "text": str, "status": str}` |

### 5.4 知识结构化模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/auto-note` | POST | 自动笔记生成 | `{"content": str, "title": str, "user_id": int}` | `{"id": int, "title": str, "content": str, "created_at": datetime}` |
| `/api/knowledge-points/{note_id}` | GET | 获取知识点 | `note_id: int` | `[{"id": int, "note_id": int, "content": str, "importance": str, "category_id": int, "created_at": datetime}]` |
| `/api/knowledge-points` | POST | 创建知识点 | `note_id: int`<br>`content: str`<br>`importance: str`<br>`category_id: int` | `{"id": int, "note_id": int, "content": str, "importance": str, "category_id": int, "created_at": datetime}` |
| `/api/categories` | GET | 获取分类 | - | `[{"id": int, "name": str, "description": str}]` |
| `/api/categories` | POST | 创建分类 | `{"name": str, "description": str}` | `{"id": int, "name": str, "description": str}` |
| `/api/knowledge-graph/generate/{note_id}` | POST | 生成知识图谱 | `note_id: int` | `{"message": str, "graph_id": int}` |
| `/api/knowledge-graph/{note_id}` | GET | 获取知识图谱 | `note_id: int` | `{"nodes": [object], "edges": [object]}` |

### 5.5 学习分析模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/study-record` | POST | 创建学习记录 | `{"user_id": int, "note_id": int, "duration": int, "date": date}` | `{"id": int, "user_id": int, "note_id": int, "duration": int, "date": date, "created_at": datetime}` |
| `/api/study-records/{user_id}` | GET | 获取学习记录 | `user_id: int` | `[{"id": int, "user_id": int, "note_id": int, "duration": int, "date": date, "created_at": datetime}]` |
| `/api/exam-points/heat` | GET | 考点热度 | - | `[{"content": str, "count": int, "heat": float}]` |
| `/api/study-plans` | POST | 创建学习计划 | `{"user_id": int, "title": str, "description": str, "start_date": date, "end_date": date, "target_hours": float}` | `{"id": int, "user_id": int, "title": str, "description": str, "start_date": date, "end_date": date, "target_hours": float, "created_at": datetime}` |
| `/api/study-plans/{user_id}` | GET | 获取学习计划 | `user_id: int` | `[{"id": int, "user_id": int, "title": str, "description": str, "start_date": date, "end_date": date, "target_hours": float, "created_at": datetime}]` |
| `/api/study-trends/{user_id}` | GET | 学习趋势 | `user_id: int`<br>`days: int` | `{"dates": [str], "hours": [float], "completion_rate": float}` |

### 5.6 学习辅助模块

| 接口 | 方法 | 功能 | 请求参数 | 成功返回 |
|------|------|------|----------|----------|
| `/api/export` | POST | 导出笔记 | `{"note_id": int, "format": str, "user_id": int}` | `{"export_id": int, "note_id": int, "format": str, "file_path": str, "created_at": datetime}` |
| `/api/export/{note_id}` | GET | 获取导出记录 | `note_id: int` | `[{"export_id": int, "note_id": int, "format": str, "file_path": str, "created_at": datetime}]` |
| `/api/reminders` | POST | 创建提醒 | `{"user_id": int, "title": str, "description": str, "remind_time": datetime, "note_id": int}` | `{"id": int, "user_id": int, "title": str, "description": str, "remind_time": datetime, "note_id": int, "is_completed": bool, "created_at": datetime}` |
| `/api/reminders/{user_id}` | GET | 获取提醒 | `user_id: int` | `[{"id": int, "user_id": int, "title": str, "description": str, "remind_time": datetime, "note_id": int, "is_completed": bool, "created_at": datetime}]` |
| `/api/reminders/{reminder_id}/status` | PUT | 更新提醒状态 | `reminder_id: int`<br>`is_completed: bool` | `{"message": str, "status": str}` |
| `/api/tools/timer` | POST | 启动计时器 | `{"duration": int, "title": str}` | `{"timer_id": int, "title": str, "duration": int, "start_time": datetime}` |
| `/api/tools/pomodoro` | POST | 启动番茄钟 | `{"work_duration": int, "break_duration": int, "cycles": int, "title": str}` | `{"pomodoro_id": int, "title": str, "work_duration": int, "break_duration": int, "cycles": int, "start_time": datetime}` |
| `/api/tools/unit-convert` | POST | 单位转换 | `{"value": float, "from_unit": str, "to_unit": str, "category": str}` | `{"value": float, "from_unit": str, "to_unit": str, "result": float, "category": str}` |
| `/api/schools/recommend` | POST | 学校推荐 | `{"score": float, "region": str, "subject": str, "ranking": int}` | `{"recommendations": [{"name": str, "rank": int, "score": float, "region": str, "subject": str, "match_score": float}]}` |

## 6. 前端集成指南

### 6.1 基础配置

1. **API 基础地址**
   - 开发环境: `http://127.0.0.1:8000/api`
   - 生产环境: `http://你的服务器地址/api`

2. **请求头配置**
   ```javascript
   const headers = {
     'Content-Type': 'application/json'
   };
   ```

3. **文件上传配置**
   ```javascript
   // 使用 FormData 上传文件
   const formData = new FormData();
   formData.append('file', file);
   formData.append('course_id', 1);
   ```

### 6.2 核心功能集成示例

#### 6.2.1 音频上传与语音转文本

```javascript
// 1. 上传音频文件
async function uploadAudio(audioFile) {
  const formData = new FormData();
  formData.append('file', audioFile);
  formData.append('course_id', 1);
  
  const response = await fetch('http://127.0.0.1:8000/api/upload/audio', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// 2. 语音转文本
async function transcribeAudio(audioId) {
  const response = await fetch('http://127.0.0.1:8000/api/asr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ audio_id: audioId })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// 使用示例
async function processAudio(audioFile) {
  try {
    // 上传音频
    const uploadResult = await uploadAudio(audioFile);
    console.log('上传成功:', uploadResult);
    
    // 语音转文本
    const transcribeResult = await transcribeAudio(uploadResult.audio_id);
    console.log('转写结果:', transcribeResult.text);
    
    return transcribeResult.text;
  } catch (error) {
    console.error('处理音频失败:', error);
    throw error;
  }
}
```

#### 6.2.2 文件上传与AI分析

```javascript
// 1. 上传文件
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('course_id', 1);
  
  const response = await fetch('http://127.0.0.1:8000/api/upload', {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// 2. AI 分析
async function analyzeContent(sourceId, sourceType, analysisType) {
  const response = await fetch('http://127.0.0.1:8000/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_id: sourceId,
      source_type: sourceType, // 'document', 'text', 'audio'
      analysis_type: analysisType // 'summary', 'keywords', 'exam_points'
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

#### 6.2.3 知识图谱生成

```javascript
// 生成知识图谱
async function generateKnowledgeGraph(noteId) {
  const response = await fetch(`http://127.0.0.1:8000/api/knowledge-graph/generate/${noteId}`, {
    method: 'POST'
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}

// 获取知识图谱
async function getKnowledgeGraph(noteId) {
  const response = await fetch(`http://127.0.0.1:8000/api/knowledge-graph/${noteId}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return await response.json();
}
```

## 7. 部署与测试

### 7.1 后端部署

1. **本地开发**
   ```bash
   # 进入项目目录
   cd d:\python_study\ZhiNote\zh-note-backend
   
   # 激活虚拟环境
   .\venv\Scripts\activate
   
   # 启动服务
   python -m uvicorn app.main:app --reload
   ```

2. **生产部署**
   - 使用 Gunicorn 或 uvicorn 作为生产服务器
   - 配置 Nginx 作为反向代理
   - 配置 HTTPS

### 7.2 前端部署

- **静态文件部署**: 部署到 CDN 或静态文件服务器
- **API 地址配置**: 根据环境配置不同的 API 基础地址
- **CORS 配置**: 后端已配置允许所有来源，生产环境可根据实际情况限制

### 7.3 测试清单

| 测试项 | 预期结果 |
|--------|----------|
| 音频文件上传 | 成功返回音频 ID |
| 语音转文本 | 成功返回识别文本 |
| PDF/DOCX 上传 | 成功返回文档 ID |
| AI 总结 | 成功返回总结结果 |
| 自动笔记生成 | 成功返回笔记内容 |
| 知识图谱生成 | 成功返回图谱数据 |
| 学习记录创建 | 成功返回记录 ID |
| 学校推荐 | 成功返回推荐结果 |
| 导出功能 | 成功生成文件 |
| 提醒功能 | 成功创建提醒 |

## 8. 故障排查

### 8.1 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `语音转文本失败: 音频转换失败` | FFmpeg 未安装或路径错误 | 安装 FFmpeg 并配置环境变量 |
| `ASR 识别失败: content len too long` | 音频超过限制 | 后端已实现分段处理，无需处理 |
| `获取 access_token 失败` | API Key 错误或网络问题 | 检查 API Key 是否正确，检查网络连接 |
| `数据库写入失败` | 数据库连接问题 | 检查 MySQL 服务是否运行，连接配置是否正确 |
| `文件解析失败` | 文件格式不支持 | 确保上传的是 PDF 或 DOCX 文件 |

### 8.2 日志查看

- **后端日志**: 查看 uvicorn 控制台输出
- **前端日志**: 查看浏览器控制台
- **数据库日志**: 查看 MySQL 错误日志

## 9. 联系与支持

- **后端开发**: 您
- **前端开发**: 您的队友
- **API 文档**: `http://127.0.0.1:8000/docs`
- **技术支持**: 如遇到问题，请查看错误信息并参考故障排查部分

## 10. 版本更新

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-04-24 | 初始版本，完成所有核心功能 |

---

**注意**: 本文档会随着项目的发展不断更新，请定期查看最新版本。