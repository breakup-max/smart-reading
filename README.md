# Smart Reading · 智阅

> 基于 LangChain + 通义千问的 PDF 智能问答系统，采用 **Hybrid Search + MMR + Cross-Encoder Rerank** 的三段式 RAG 架构，支持多轮对话。

---

## ✨ 特性

| 能力 | 实现方式 |
|:---|:---|
| 📄 PDF 解析 | PyMuPDFLoader |
| ✂️ 文本切分 | RecursiveCharacterTextSplitter（递归按段落→句子→词切） |
| 📐 向量模型 | DashScope `text-embedding-v1`（1536 维） |
| 💾 向量存储 | Chroma（本地持久化） |
| 🔍 检索策略 | **Dense + BM25 混合检索**，MMR 去重保多样性 |
| 🎯 精排 | Cross-Encoder LLM Rerank（粗召回 30 → 精排 Top 4） |
| 🔄 多轮改写 | 结合对话历史对指代消解问题重写查询 |
| 🤖 生成模型 | 通义千问 `qwen3-max` |
| 💬 交互方式 | 命令行交互，支持多轮对话 |

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                           run.py                                 │
│                   入口 · 命令行交互                               │
└────────┬────────────────────────────────────────────────────────┘
         │
    ┌────▼────┐        ┌────────────────────────────────────┐
    │ Indexing │        │              Querying              │
    │ Pipeline │        │         （RAG Pipeline）             │
    ├─────────┤        ├────────────────────────────────────┤
    │  ingest │        │  rewrite    → 多轮问题改写           │
    │ storage │        │  retriever  → 混合检索 + MMR        │
    │ vector  │        │  rerank     → Cross-Encoder 精排    │
    │  store  │        │  answer     → LLM 生成答案          │
    └────┬────┘        └────────────────────────────────────┘
         │                         │
         └──────────┬──────────────┘
                    ▼
                ChromaDB
             （向量索引）
```

### 检索三段式

```
用户提问
    │
    ▼
┌───────────────┐
│  Rewrite       │  多轮对话问题改写（指代消解）
└───────┬───────┘
        ▼
┌───────────────┐
│  Retrieve      │  混合检索：Dense Vector + BM25 → MMR 去重 → 召回 K=30
└───────┬───────┘
        ▼
┌───────────────┐
│  Rerank        │  Cross-Encoder 精排 → Top 4
└───────┬───────┘
        ▼
┌───────────────┐
│  Generate      │  构造 Prompt → qwen3-max 生成最终答案
└───────────────┘
```

---

## 📦 安装

### 环境要求

- Python ≥ 3.10
- 通义千问 API Key（阿里云百炼平台）

### 依赖安装

```bash
pip install -r requirements.txt
```

### 配置 API Key

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY = "your-api-key-here"

# Windows CMD
set DASHSCOPE_API_KEY=your-api-key-here

# Linux / macOS
export DASHSCOPE_API_KEY="your-api-key-here"
```

---

## 🚀 快速开始

### 方式一：Web 界面（推荐）

```bash
# Windows
start.bat

# Linux / macOS
bash start.sh
```

浏览器打开 **http://localhost:8000**，上传 PDF 即可对话问答。

### 方式二：命令行

```bash
python run.py "D:\我的文档\paper.pdf"
```

支持传入文件路径或文件夹路径（自动扫描目录下 PDF）。

### 方式三：Docker 部署

```bash
# 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY

# 构建并启动
docker compose up -d
```

浏览器打开 **http://localhost:8000**。

---

## 📁 目录结构

```
smart-reading/
├── run.py                          # CLI 入口，PDFQA 类
├── start.bat / start.sh            # 一键启动脚本
├── Dockerfile / docker-compose.yml # Docker 部署
├── .env.example                    # 环境变量模板
├── web/                            # Web 前后端
│   ├── app.py                      # FastAPI 应用入口
│   ├── schemas.py                  # Pydantic 数据模型
│   ├── routers/
│   │   ├── upload.py               # POST /api/upload
│   │   └── chat.py                 # POST /api/chat
│   └── static/
│       ├── index.html              # 前端主页面
│       ├── css/style.css
│       └── js/app.js
├── config/
│   └── setting.py                  # QaConfig：所有可调超参数
├── indexing/                       # 索引构建层
│   ├── indexing_pipeline.py
│   ├── ingest.py
│   ├── vectorstore.py
│   └── storage.py
├── querying/                       # 查询问答层
│   ├── rag_pipeline.py
│   ├── rewrite.py
│   ├── vector_retriever.py
│   ├── rerank.py
│   ├── query_prompt.py
│   └── answer.py
├── test/                           # 测试脚本 & 学习实验
├── data/
├── requirements.txt
└── .gitignore
```

---

## ⚙️ 参数调优

所有超参数集中在 `config/setting.py`：

```python
@dataclass(frozen=True)
class QaConfig:
    llm_model: str = "qwen3-max"        # 通义千问模型版本
    llm_temperature: float = 0.2        # 生成温度（越低越保守）
    embedding_model: str = "text-embedding-v1"  # Embedding 模型
    chunk_size: int = 800               # 文本块大小
    chunk_overlap: int = 120            # 相邻块重叠
    context_max_chars: int = 1400       # 送入 LLM 的最大上下文长度
    chroma_root_dir: str = ".chroma"    # 向量库持久化目录
```

调用 `rag_pipeline` 时也可动态指定检索参数（在 `run.py` 的 `ask()` 方法中）：

```python
top_k=4          # 精排后保留的文档数
recall_k=30      # 粗召回候选数
hybrid_top_m=12  # 混合检索融合后的候选数
```

---

## 🔬 技术细节

> 以下内容为 RAG 相关原理的学习笔记，包含完整的代码示例和推导过程。

- [Native RAG 原理：索引构建 + 检索生成](#1-native-rag)
- [MMR：解决检索结果冗余问题](#2-mmr)
- [Hybrid Search：Dense Vector + BM25 混合检索](#3-hybrid-search)

---

### 1. Native RAG

详见原 README 的「1. Native RAG原理」章节，涵盖：
- **索引构建三步骤**：文本拆分 → 文本向量化 → 向量存储
- **RecursiveCharacterTextSplitter** 的递归降级切分策略（含完整推导示例）
- **文本向量化**原理 + 余弦相似度代码验证
- **Chroma** 向量数据库基础操作
- **检索增强生成三步骤**：向量检索 → 增强提示 → 答案生成

### 2. MMR

详见原 README 的「2. MMR」章节，涵盖：
- 为什么纯相似度检索会出现信息冗余
- MMR 的相关性 / 多样性平衡原理
- `lambda_mult` 参数的作用
- Chroma `max_marginal_relevance_search()` 的代码对比实验

### 3. Hybrid Search

详见原 README 的「3. Hybrid Search」章节，涵盖：
- Dense Vector vs BM25 关键词检索的优劣势互补
- 为什么"GPT-4 参数量"向量检索会排错
- 混合检索的融合策略

---

## 🚢 部署上线

### 本地部署

```bash
# 1. 设置环境变量
set DASHSCOPE_API_KEY=sk-xxx

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
# 或双击 start.bat（Windows）/ bash start.sh（Linux）
```

### Docker 部署

```bash
cp .env.example .env
# 编辑 .env → 填入 DASHSCOPE_API_KEY
docker compose up -d
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 前端页面 |
| `/api/health` | GET | 健康检查 |
| `/api/upload` | POST | 上传 PDF（multipart/form-data，file 字段） |
| `/api/chat` | POST | 提问（JSON：file_hash + question） |

### 云平台部署

项目可直接部署到任何支持 Python 的云平台（Railway、Render、HuggingFace Spaces 等），只需设置 `DASHSCOPE_API_KEY` 环境变量并将启动命令设为：

```
python -m uvicorn web.app:app --host 0.0.0.0 --port $PORT
```

---

## 📝 License

MIT