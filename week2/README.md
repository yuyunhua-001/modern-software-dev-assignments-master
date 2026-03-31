# Week 2 – Test Factor Extractor

需求分析助手：基于 FastAPI + SQLite + Ollama 的应用，可将自由格式的需求文档转换为结构化需求点与测试因子，辅助测试用例设计。

## 项目概述

本应用提供：

- **需求理解**：使用 LLM 将非结构化需求文档重述为分类清晰的需求点（category + summary）
- **测试因子提取**：启发式或 LLM 提取可测试维度（如文件格式、权限、数据限制等）
- **笔记与因子管理**：保存需求文档、测试因子，并支持标记用例是否已设计

技术栈：FastAPI、SQLite、Ollama（本地 LLM）、Pydantic。

## 环境要求

- Python 3.10+
- [Ollama](https://ollama.com/)（本地运行 LLM，推荐 `qwen3.5:4b` 或类似模型）
- Poetry（依赖管理）

## 安装与运行

### 1. 安装依赖

在项目根目录执行：

```bash
poetry install
```

### 2. 启动 Ollama（可选，用于 LLM 功能）

```bash
ollama pull qwen3.5:4b
ollama run qwen3.5:4b
```

### 3. 配置环境变量（可选）

在项目根目录创建 `.env` 文件，可配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OLLAMA_HOST` | Ollama 服务地址 | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | 使用的模型名称 | `qwen3.5:4b` |
| `OLLAMA_EXTRACT_TIMEOUT` | LLM 调用超时（秒） | `300` |
| `OLLAMA_THINK` | 是否启用思考模式（`1`/`true`/`yes`） | 空 |

### 4. 启动服务

```bash
poetry run uvicorn week2.app.main:app --reload
```

浏览器访问：<http://127.0.0.1:8000/>

## API 端点

### 根路径

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回前端 HTML 页面 |

### Notes（笔记）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/notes` | 创建笔记。请求体：`{"content": "..."}` |
| GET | `/notes/{note_id}` | 获取单条笔记 |

### Test Factors（测试因子）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/test-factors/analyze` | 分析需求：并行执行「需求理解」+「测试因子提取」。请求体：`{"text": "...", "save_doc": true}` |
| POST | `/test-factors/extract` | 仅提取测试因子（不含需求理解）。请求体：`{"text": "...", "save_doc": true}` |
| GET | `/test-factors` | 列出所有测试因子。可选查询参数：`doc_id` 按文档过滤 |
| POST | `/test-factors/{factor_id}/covered` | 标记因子是否已设计用例。请求体：`{"covered": true}` |

### 请求/响应示例

**POST /test-factors/analyze**

```json
// 请求
{"text": "用户上传头像，格式 jpg/png，大小不超过 2MB。", "save_doc": true}

// 响应
{
  "doc_id": 1,
  "requirements": [{"category": "文件上传", "summary": "支持 jpg/png，限制 2MB"}],
  "factors": [{"id": 1, "factor": "文件格式"}, {"id": 2, "factor": "文件大小限制"}]
}
```

## 运行测试

在项目根目录执行：

```bash
python -m pytest week2/tests/test_extract.py -v
```

运行 week2 下所有测试：

```bash
python -m pytest week2/tests/ -v
```

**注意**：请从项目根目录运行 pytest，不要直接执行 `python week2/tests/test_extract.py`，否则相对导入会失败。

## 项目结构

```
week2/
├── app/
│   ├── main.py          # FastAPI 应用入口
│   ├── db.py            # SQLite 数据库操作
│   ├── routers/
│   │   ├── notes.py     # 笔记 API
│   │   └── test_factors.py  # 测试因子 API
│   └── services/
│       └── extract.py   # 启发式 + LLM 提取逻辑
├── frontend/
│   └── index.html       # 前端页面
├── tests/
│   └── test_extract.py  # 提取服务单元测试
└── data/                # SQLite 数据库目录（自动创建）
```

## 数据库

使用 SQLite，数据文件位于 `week2/app/data/app.db`。表结构：

- **notes**：需求文档内容
- **test_factors**：测试因子，可关联 `doc_id` 到 notes
