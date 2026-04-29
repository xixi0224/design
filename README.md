# ZhiNote API Guide

ZhiNote 是一个用于文档上传、文本提取、AI 分析、笔记生成和可视化展示的项目。

当前后端接口已基本稳定，前端可以根据以下说明开始开发和联调。

---

## 项目目标

### 后端负责
- 接收文档上传。
- 提取文档文本内容。
- 调用 AI 进行结构化分析。
- 将分析结果写入数据库。
- 提供前端可直接渲染的 JSON 数据接口。

### 前端负责
- 上传页面。
- 分析结果页面。
- 笔记展示页面。
- 可视化展示页面。

---

## 技术栈

- Python
- FastAPI
- PyMySQL
- pdfplumber
- python-docx
- DashScope / Qwen

---

## 启动方式

在项目根目录执行：

```bash
uvicorn app.main:app --reload
```

启动后默认访问：

```text
http://127.0.0.1:8000
```

接口文档地址：

```text
http://127.0.0.1:8000/docs
```

---

## 目录结构

```text
ZhiNote/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── db.py
│   ├── config.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── notes.py
│   │   ├── visualization.py
│   │   └── animation.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── text_extract.py
│   │   └── ai_service.py
│   └── utils/
│       ├── __init__.py
│       └── db_helpers.py
├── uploads/
└── README.md
```

---

## 接口说明

### 1. 上传文档

**接口地址**

```text
POST /api/upload
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | file | 是 | 文档文件，支持 pdf、docx、txt、md |
| course_id | int | 否 | 课程 ID，默认值为 1 |

**返回示例**

```json
{
  "message": "上传成功",
  "doc_id": 1,
  "filename": "sample.docx",
  "text_length": 1234
}
```

**说明**

- `doc_id` 是后续分析、笔记和图表接口的核心参数。
- 上传成功后，会在 `zhinote_documents` 表中新增记录。

---

### 2. 分析文档

**接口地址**

```text
POST /api/analyze/{doc_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| doc_id | int | 是 | 文档 ID |

**返回示例**

```json
{
  "message": "分析完成",
  "count": 2,
  "results": [
    {
      "section": "第一章",
      "summary": "内容摘要",
      "keywords": ["关键词1", "关键词2"],
      "is_exam_point": true,
      "importance": "⭐⭐"
    }
  ]
}
```

**说明**

- 该接口负责调用 AI 对文档进行结构化分析。
- 分析结果会写入 `zhinote_analysis` 表。
- 如果 `count = 0`，说明本次分析没有生成可写入的结果，需要检查输入内容或分析逻辑。

---

### 3. 获取笔记

**接口地址**

```text
GET /api/notes/{doc_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| doc_id | int | 是 | 文档 ID |

**返回示例**

```json
{
  "doc_id": 1,
  "notes": [
    {
      "section": "第一章",
      "summary": "内容摘要",
      "keywords": ["关键词1", "关键词2"],
      "is_exam_point": true,
      "importance": "⭐⭐"
    }
  ]
}
```

**前端用途**

- 直接渲染笔记卡片。
- 可用于列表页、详情页、复习页等。

---

### 4. 获取可视化数据

**接口地址**

```text
GET /api/visualization/{doc_id}
```

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| doc_id | int | 是 | 文档 ID |

**返回示例**

```json
{
  "bar_data": [
    {
      "name": "考点1",
      "value": 3
    }
  ],
  "word_cloud": [
    {
      "name": "关键词1",
      "value": 5
    }
  ]
}
```

**前端用途**

- `bar_data`：用于柱状图。
- `word_cloud`：用于词云展示。
- 前端可以直接拿来渲染，不需要再做复杂转换。

---

### 5. 动画测试接口

**接口地址**

```text
GET /api/animation
```

**查询参数**

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 动画关键词，默认值为“栈” |

**返回示例**

```json
{
  "type": "stack",
  "steps": [
    {
      "action": "push",
      "value": "A"
    },
    {
      "action": "push",
      "value": "B"
    },
    {
      "action": "pop"
    }
  ]
}
```

---

## 前端对接建议

前端开发时，优先依赖以下字段：

- `doc_id`
- `message`
- `status`
- `notes`
- `bar_data`
- `word_cloud`
- `count`
- `results`

建议页面开发顺序：

1. 上传页。
2. 分析结果页。
3. 笔记页。
4. 图表页。

---

## 数据库说明

### zhinote_documents
用于存储上传后的文档信息。

常见字段：
- `id`
- `course_id`
- `filename`
- `content`
- `page_count`
- `status`

### zhinote_analysis
用于存储 AI 分析后的结构化结果。

常见字段：
- `id`
- `doc_id`
- `section`
- `summary`
- `keywords`
- `is_exam_point`
- `importance`

---

## 常见问题

### 1. 上传成功，但分析结果为空
请检查：
- 文档内容是否正确提取。
- AI 返回是否为空。
- 分析逻辑是否正常执行。

### 2. `zhinote_analysis` 没有新增记录
请检查：
- `/api/analyze/{doc_id}` 是否真正调用成功。
- 数据库插入是否报错。
- `doc_id` 是否正确。

### 3. 前端跨域请求失败
请确认后端已开启 CORS，并允许前端地址访问。

---

## 注意事项

- 前后端开发时，请尽量保持接口字段稳定。
- 如果后端需要修改返回结构，请提前同步给前端。
- 当前项目仍在持续开发中，后续可能会继续扩展课程管理、搜索和更多可视化功能。