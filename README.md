<p align="center">
  <h1 align="center">Smart Reading · 智阅</h1>
  <p align="center">
    <strong>面向 PDF 文档智能的生产级 RAG 系统</strong>
    <br/>
    混合搜索 + MMR + Cross-Encoder 重排序 · 多轮对话 · Web 界面
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
  <img src="https://img.shields.io/badge/LangChain-1.4+-orange.svg" alt="LangChain"/>
  <img src="https://img.shields.io/badge/LLM-Qwen3--Max-8A2BE2.svg" alt="LLM"/>
</p>

---

## 项目概述

Smart Reading（智阅）是一个**全栈 RAG（检索增强生成）应用**，专为深度文档问答而设计。它能够解析 PDF 文档，构建可搜索的向量索引，并以**带有证据支撑、可溯源引用**的方式回答用户问题 —— 而不仅仅是生成文本。

不同于简单的"PDF 聊天"演示，本系统实现了**三阶段检索流水线**，包含混合搜索、多样性感知的 MMR 去重、Cross-Encoder LLM 重排序以及多轮查询改写。项目同时提供 **Web 界面**和 **CLI 命令行**两种交互方式，并支持 Docker 容器化部署。

### 核心差异对比

| 维度 | 普通 Demo | Smart Reading |
|------|-----------|---------------|
| 检索方式 | 单一向量相似度 | 稠密向量 + BM25 混合检索，MMR 去重 |
| 重排序 | 无或仅 TF-IDF | Cross-Encoder LLM，0-10 分打分 |
| 多轮对话 | 无状态 | 上下文感知的查询改写，自动消解代词 |
| 证据展示 | 仅显示答案 | 结构化证据，含页码、来源、分数元数据 |
| 工程化部署 | `python app.py` | Docker Compose、健康检查、环境变量驱动配置 |
| 交互界面 | 仅 CLI | Web UI + CLI 双模式 |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                            入口层                                    │
│                   Web UI (FastAPI)  │  CLI (run.py)                  │
└──────────────────┬──────────────────┴────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         RAG 流水线                                   │
│                                                                      │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────┐          │
│  │  查询改写 │───▶│     混合检索      │───▶│    重排序      │──▶ 生成 │
│  │          │    │  稠密 + BM25     │    │  混合打分       │          │
│  │ 上下文   │    │  MMR 去重        │    │  LLM 评判      │          │
│  │ 感知     │    │  Recall K=30     │    │  Top N=4       │          │
│  └──────────┘    └──────────────────┘    └───────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                   │                              │
                   ▼                              ▼
            ┌──────────┐                 ┌──────────────┐
            │ ChromaDB │                 │  Qwen3-Max   │
            │ (向量库) │                 │  (LLM 生成)  │
            └──────────┘                 └──────────────┘
```

### 流水线阶段说明

1. **查询改写** —— 使用 LLM 驱动的上下文改写，消解多轮对话中的代词、缩写和隐式引用
2. **混合检索** —— 融合稠密向量相似度（DashScope `text-embedding-v1`，1536 维）与 BM25 关键词匹配；应用 MMR（最大边际相关性）确保结果多样性
3. **Cross-Encoder 重排序** —— 两阶段：(a) 混合打分融合向量相似度 + Jaccard 文本重叠度，并结合长度/关键词启发式规则，(b) LLM 对每个候选进行 0-10 相关性打分，仅保留 Top-4
4. **证据驱动生成** —— 构建包含编号证据块的结构化 Prompt，每块附带来源文档和页码元数据，最终通过 Qwen3-Max 生成答案

---

## 功能特性

### 核心能力

- **PDF 解析** —— 基于 PyMuPDF 解析，配合 `RecursiveCharacterTextSplitter`（段落 → 句子 → Token 三级回退策略）
- **三阶段 RAG** —— 查询改写 → 混合检索 + MMR → Cross-Encoder LLM 重排序 → 答案生成
- **多轮对话** —— 自动维护聊天历史，结合上下文进行查询改写
- **证据溯源** —— 每条答案都包含结构化证据元数据：内容、来源文件、页码、向量分数、混合分数和 LLM 相关性分数
- **可配置流水线** —— 所有超参数集中在 `QaConfig` 数据类中；检索深度（`recall_k`、`hybrid_top_m`、`top_k`）可按查询动态调整

### 交互界面

- **Web UI** —— 单页聊天应用，支持 PDF 上传、对话历史以及证据展开/折叠
- **CLI 命令行** —— 交互式终端模式，支持文件选择对话框和目录级 PDF 扫描
- **REST API** —— `POST /api/upload`、`POST /api/chat`、`GET /api/health` —— 可直接对接集成

### 工程特性

- **会话隔离** —— 通过内容哈希命名空间支持多个并发 PDF 会话
- **持久化索引** —— ChromaDB 存储于本地文件系统；一次建索引，多次查询
- **懒加载初始化** —— 向量索引在首次查询时构建，而非启动时
- **Docker 支持** —— `Dockerfile` + `docker-compose.yml`，Chroma 数据卷持久化
- **热重载** —— Uvicorn 配合 `--reload` 开发模式

---

## 快速开始

### 前置条件

- Python ≥ 3.10
- [DashScope API Key](https://bailian.console.aliyun.com/)（阿里云百炼模型平台）

### 安装

```bash
git clone https://github.com/breakup-max/smart-reading.git
cd smart-reading
pip install -r requirements.txt
```

### 配置 API Key

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "sk-your-key"

# Linux / macOS
export DASHSCOPE_API_KEY="sk-your-key"
```

### 启动

**Web 界面**（推荐）：

```bash
# Windows
start.bat

# Linux / macOS
bash start.sh

# 或手动启动：
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

打开浏览器访问 **http://localhost:8000**，上传 PDF 即可开始提问。

**CLI 命令行**：

```bash
python run.py "/path/to/document.pdf"
```

**Docker 部署**：

```bash
cp .env.example .env        # 编辑并设置 DASHSCOPE_API_KEY
docker compose up -d
```

---

## API 接口

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/health` | `GET` | 健康检查；返回 `{"status": "ok", "api_key_configured": true}` |
| `/api/upload` | `POST` | 上传 PDF（`multipart/form-data`，字段：`file`）。返回用于后续对话的 `file_hash` |
| `/api/chat` | `POST` | 发送问题（`application/json`，字段：`file_hash`、`question`）。返回答案和证据 |

### 请求示例

```bash
# 上传 PDF
curl -F "file=@paper.pdf" http://localhost:8000/api/upload
# → {"file_hash": "a1b2c3...", "message": "索引构建完成"}

# 开始对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"file_hash": "a1b2c3...", "question": "这篇论文的核心贡献是什么？"}'
# → {"answer": "...", "evidence": [...], "rewritten": true}
```

---

## 配置说明

所有可调参数集中在 [`config/setting.py`](config/setting.py)：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `llm_model` | `qwen3-max` | 用于生成和重排序的 Qwen 模型版本 |
| `llm_temperature` | `0.2` | 生成温度（越低越确定） |
| `embedding_model` | `text-embedding-v1` | DashScope 嵌入模型（输出 1536 维） |
| `chunk_size` | `800` | 文本分块大小（字符数） |
| `chunk_overlap` | `120` | 相邻分块之间的重叠 |
| `context_max_chars` | `1400` | 送入 LLM 的最大上下文长度 |
| `chroma_root_dir` | `.chroma` | ChromaDB 持久化目录 |

单次查询级别的检索参数（传递给 `RagPipeline.query()`）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | `4` | 重排序后最终保留的文档数 |
| `recall_k` | `30` | 初始粗召回候选池大小 |
| `hybrid_top_m` | `12` | 混合重排序后保留的候选数 |

---

## 项目结构

```
smart-reading/
├── run.py                     # CLI 入口 + PDFQA 核心类
├── start.bat / start.sh       # 一键启动脚本
├── Dockerfile                 # 容器镜像定义
├── docker-compose.yml         # 多服务编排
├── .env.example               # 环境变量模板
│
├── web/                       # Web 应用层
│   ├── app.py                 # FastAPI 应用，会话管理
│   ├── schemas.py             # Pydantic 请求/响应模型
│   ├── routers/
│   │   ├── upload.py          # POST /api/upload
│   │   └── chat.py            # POST /api/chat
│   └── static/
│       ├── index.html         # 聊天界面
│       ├── css/style.css
│       └── js/app.js
│
├── config/
│   └── setting.py             # QaConfig：集中式超参数配置
│
├── indexing/                  # 离线索引构建
│   ├── indexing_pipeline.py   # 编排器：ingest → vectorstore
│   ├── ingest.py              # PDF 加载 + 递归分块
│   ├── vectorstore.py         # Embedding + ChromaDB 存储
│   └── storage.py             # 命名空间与持久化管理
│
├── querying/                  # 在线查询流水线
│   ├── rag_pipeline.py        # 编排器：rewrite → retrieve → rerank → generate
│   ├── rewrite.py             # 多轮查询改写
│   ├── vector_retriever.py    # 稠密向量召回（带分数）
│   ├── rerank.py              # 两阶段重排序（混合打分 + LLM 评判）
│   ├── query_prompt.py        # Prompt 模板
│   └── answer.py              # LLM 答案生成
│
├── test/                      # 测试脚本与实验
├── requirements.txt
└── .gitignore
```

---

## 技术深挖

### 混合检索

本系统**不**仅依赖向量相似度，而是融合了两个互补信号：

- **稠密向量** —— 通过 1536 维 DashScope Embedding 捕获语义含义
- **BM25 关键词** —— 捕获精确术语匹配，对专业术语、缩写和数值引用至关重要

融合发生在重排序阶段而非检索阶段，从而允许更细致的打分逻辑。

### 混合重排序算法

在进入 LLM 评判之前，候选分块先通过启发式混合打分器：

```
hybrid_score = 0.3 × vector_score + 0.7 × jaccard_overlap_score

调整规则：
  - len(text) < 80 字符  → × 0.8 （太短 = 信息量不足）
  - len(text) > 1600 字符 → × 0.9 （太长 = 相关性被稀释）
  - 存在关键词重叠        → × 1.1 （奖励精确术语匹配）
```

这在昂贵的 LLM 重排序之前，平衡了语义相关性与词法精确性。

### LLM Cross-Encoder 重排序

每个候选分块由 Qwen3-Max 使用结构化 Prompt 单独进行 0-10 打分。模型评估的是**与查询的相关性**，而非表面相似度。仅 Top-N 分块进入答案生成，确保 LLM 看到的是最有用的上下文。

### 证据可溯源性

每条答案都可以溯源到其来源。API 返回结构如下：

```json
{
  "answer": "...",
  "evidence": [
    {
      "content": "原文片段...",
      "source": "paper.pdf",
      "page": 3,
      "vector_score": 0.87,
      "hybrid_score": 0.92,
      "llm_score": 9.0
    }
  ],
  "rewritten": true,
  "search_query": "这篇论文的核心贡献..."
}
```

这种设计使得系统适用于需要**可审计性**的场景 —— 学术研究、法律文档审阅、合规检查等。

---

## 部署

### 自托管

```bash
# 设置环境变量并启动
export DASHSCOPE_API_KEY="sk-your-key"
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
cp .env.example .env   # 配置 API Key
docker compose up -d    # 访问 http://localhost:8000
```

### 云平台部署

应用遵循标准 ASGI 接口，可部署到任何支持 Python Web 应用的平台（Railway、Render、Hugging Face Spaces 等）。启动命令为：

```
python -m uvicorn web.app:app --host 0.0.0.0 --port $PORT
```

仅需一个环境变量：`DASHSCOPE_API_KEY`。

---

## 依赖说明

| 包名 | 用途 |
|------|------|
| `langchain` | RAG 编排框架 |
| `langchain-chroma` | ChromaDB 向量库集成 |
| `chromadb` | 向量数据库（本地持久化） |
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `python-multipart` | 文件上传解析 |
| `numpy` | 数值运算 |

---

## 未来规划

- [ ] SSE 流式响应，支持实时答案生成
- [ ] 多文件对话 —— 同时跨多个 PDF 进行问答
- [ ] 用户认证与会话持久化
- [ ] Kubernetes 部署清单
- [ ] LangSmith / LangFuse 可观测性集成
- [ ] 支持 `.docx`、`.txt` 和 Web URL  ingestion

---

## 许可证

MIT —— 详见 [LICENSE](LICENSE) 文件。