# Smart-Reading 前后端交互方案分析文档

---

## 一、当前项目现状

### 1.1 项目定位
Smart-Reading 是一个基于 **RAG（检索增强生成）** 的 PDF 智能问答系统，用户上传 PDF 后可通过自然语言提问，系统基于 PDF 内容生成答案。

### 1.2 技术栈（现有）
| 层级 | 技术 | 版本 |
|------|------|------|
| LLM | 通义千问 (qwen3-max) | DashScope |
| Embedding | text-embedding-v1 | DashScope |
| 向量库 | ChromaDB | 1.5.9 |
| 框架 | LangChain | 1.4.0 |
| 交互方式 | 纯命令行 (CLI) | input() |

### 1.3 核心模块
```
smart-reading/
├── run.py                  # 入口 + PDFQA 类（核心封装）
├── config/setting.py       # QaConfig 配置（dataclass）
├── indexing/               # 索引构建流水线
│   ├── indexing_pipeline.py    # 主流程：PDF -> 切分 -> Embedding -> Chroma
│   ├── ingest.py               # PDF 加载与切分
│   ├── vectorstore.py          # Chroma 向量库管理
│   └── storage.py              # PDF 字节落盘 + MD5 哈希
└── querying/               # 查询流水线
    ├── rag_pipeline.py         # RAG 主流水线
    ├── rewrite.py              # 查询改写
    ├── vector_retriever.py     # 向量召回
    ├── rerank.py               # 混合检索 + Rerank
    ├── answer.py               # 答案生成
    └── query_prompt.py         # Prompt 模板
```

### 1.4 核心 API（待包装）
```python
# run.py 中的 PDFQA 类 —— 这就是我们要暴露给前端的核心逻辑
pdfqa = PDFQA(pdf_bytes, api_key)
pdfqa._build_index()                      # 首次构建索引（懒加载）
result = pdfqa.ask("问题内容")             # 返回 dict: {answer, context, evidence, search_query, rewritten}
```

### 1.5 当前痛点
- 只有命令行，无法在浏览器中使用
- 无法上传 PDF 文件（只能本地路径）
- 没有对话界面体验
- 无法查看引用的证据片段
- 没有流式输出响应

---

## 二、GitHub 同类项目架构调研

### 2.1 主流架构模式（三梯队）

经过对 GitHub 上 RAG/PDF Chatbot 类项目（star 数从几百到几万不等）的检索，归纳出 **三种常见的前后端架构**：

#### 第一梯队：生产级全栈分离架构
```
+-------------+   HTTP/REST   +-------------+   本地调用   +---------------+
|  前端 SPA    | ----------->  |  后端 API    | -----------> |  RAG Pipeline  |
| (React/Vue)  | <----------- | (FastAPI)    | <----------- |  (LangChain)   |
+-------------+               +-------------+               +---------------+
      |                             |                              |
      v                             v                              v
  Axios/fetch                   Pydantic 校验                   ChromaDB
  流式 (SSE/WebSocket)            文件上传 API                 DashScope
```

**代表项目**：
| 项目 | Star | 前端 | 后端 | 特点 |
|------|------|------|------|------|
| RagChatBot (github.com/RohitOruganti/ragchatbot) | 高 | React + Vite + Tailwind | FastAPI + Uvicorn | 标准前后端分离 |
| Azure Search OpenAI Demo (github.com/Azure-Samples/) | 高 | Next.js | Python FastAPI | 微软官方推荐方案 |
| agentic-rag-core (github.com/phodal/rag) | 中 | React | Flask/FastAPI | 带 REST API 封装 |

**优点**：专业、可扩展、可独立部署前后端、适合生产
**缺点**：需要同时维护两套代码、前端需要额外技能

---

#### 第二梯队：Python 一体化 UI 框架（纯 Python）
```
+------------------------------------------------------+
|                 单一 Python 进程                       |
|  +------------+        +--------------+               |
|  | UI 框架     | -----> | RAG Pipeline  |               |
|  |(Streamlit  |        |  (LangChain)  |               |
|  | Gradio      |        |               |               |
|  | Chainlit)   | <----- |               |               |
|  +------------+        +--------------+               |
|         |                      |                       |
|         v                      v                       |
|    自动渲染网页            ChromaDB + DashScope        |
+------------------------------------------------------+
```

**代表项目**：
| 项目 | 框架 | 特点 |
|------|------|------|
| My-Chat-LangChain | Streamlit | 掘金热门教程配套 |
| HuggingFace Spaces RAG Demo | Gradio | HF 官方推荐 ML Demo 方式 |
| Chainlit RAG Examples | Chainlit | 原生对话 UI + 流式输出 |

**优点**：零前端代码、几行 Python 就能出网页 UI、开发速度极快
**缺点**：自由度低、UI 定制有限、不适合做复杂交互

---

#### 第三梯队：简单 Flask + 原生 HTML
```
+-------------+   HTTP   +-------------+   本地调用   +---------------+
| HTML + JS   | -------> | Flask 后端    | -----------> | RAG Pipeline  |
| (原生/轻量)  | <------- |              | <----------- |               |
+-------------+          +-------------+               +---------------+
```

**优点**：概念简单、学习成本低
**缺点**：UI 体验一般、需要自己写 HTML/CSS/JS

---

### 2.2 UI 框架对比详细表

| 维度 | Streamlit | Gradio | Chainlit | FastAPI + React | Flask + HTML |
|------|-----------|--------|----------|-----------------|-------------|
| 开发速度 | 极快 | 极快 | 快 | 慢 | 中等 |
| 学习曲线 | 低 | 很低 | 低 | 高(React) | 中等 |
| UI 美观度 | 中等 | 中等 | 较好 | 可自由定制 | 需自己写CSS |
| 聊天体验 | 基础 | 基础 | 专业级 | 完美 | 一般 |
| 文件上传 | 原生支持 | 原生支持 | 原生支持 | 需写接口 | 需写接口 |
| 流式输出 | 支持 | 支持 | 原生支持 | SSE/WebSocket | 需自己实现 |
| 证据/来源展示 | 方便 | 方便 | 原生支持 | 自由定制 | 需自己实现 |
| 生产部署 | 适合Demo | HF Spaces方便 | 可Docker | 完全可控 | 完全可控 |
| 代码侵入性 | 需改造结构 | 中等 | 中等 | 包装类即可 | 包装类即可 |

---

## 三、三种可选方案

### 方案 A：FastAPI + 原生 HTML（推荐）

```
项目结构：
smart-reading/
├── run.py                  # 原 CLI 入口（保留）
├── web/                    # 新增 Web 层
│   ├── app.py                 # FastAPI 应用入口
│   ├── routers/               # API 路由
│   │   ├── upload.py          # POST /api/upload  (上传 PDF)
│   │   └── chat.py            # POST /api/chat    (提问)
│   ├── schemas.py             # Pydantic 数据模型
│   └── static/                # 前端静态文件
│       ├── index.html         # 主页面
│       ├── css/style.css
│       └── js/app.js
├── config/                  # 保留不动
├── indexing/                # 保留不动
└── querying/                # 保留不动
```

**新增依赖**：
```
fastapi
uvicorn[standard]
python-multipart
```

**最小 API 设计**：
| 端点 | 方法 | 功能 |
|------|------|------|
| /api/upload | POST | 上传 PDF，返回 file_hash（触发索引构建） |
| /api/chat | POST | 传入 file_hash + question，返回 answer + evidence |
| /api/health | GET | 健康检查 |

**优点**：
- 最贴合现有架构：只需包装 PDFQA 类，核心代码零改动
- 依赖最少：FastAPI + uvicorn + python-multipart，3 个新包
- 无需前端构建：原生 HTML/JS/CSS，一个文件搞定前端
- 可扩展性好：后续想换 React/Vue 只需替换 static/ 目录
- 开发效率高：预计 2-3 小时完成基础版

---

### 方案 B：Streamlit

```
项目结构：
smart-reading/
├── run.py                  # 原 CLI 入口（保留）
├── streamlit_app.py        # 新增 Streamlit 入口
├── config/                  # 保留不动
├── indexing/                # 保留不动
└── querying/                # 保留不动
```

**新增依赖**：
```
streamlit
```

**优点**：
- 开发速度最快：1 个新包，一个文件就能跑
- 文件上传原生支持
- 对话 UI 原生支持
- 证据展示方便（st.expander）

**缺点**：
- 需要适配 Streamlit 的 session_state 机制
- UI 风格固定，定制有限
- 每次交互可能重新运行脚本

---

### 方案 C：Chainlit

**新增依赖**：
```
chainlit
```

**优点**：
- 对话 UI 最专业：原生支持多轮对话、消息气泡、流式输出
- 证据/来源原生支持
- 支持中间步骤展示

**缺点**：
- Chainlit 团队 2025 年 5 月收缩（社区活跃度可能下降）
- 需要学习装饰器模式

---

## 四、推荐方案：A（FastAPI + 原生 HTML）

### 4.1 推荐理由

1. **与现有项目解耦最好**：只需在 PDFQA 类外面包一层 HTTP 接口，config/indexing/querying 完全不动

2. **依赖最少、最轻量**：只新增 3 个包，不引入重型前端工具链

3. **符合项目学习/实验定位**：FastAPI 是 Python 后端现代标准，学会了受用终身；原生 HTML/JS/CSS 是 Web 基础

4. **扩展性最好**：未来想换 React/Vue 只需替换 static/ 目录；加用户系统 FastAPI 生态有现成方案；流式输出用 StreamingResponse 天然支持

5. **核心代码几乎零改动**：PDFQA 类的 __init__、_build_index、ask 方法签名不变；原有的 CLI 测试、单元测试全部不受影响

### 4.2 实施路径（建议分 3 步）

| 步骤 | 内容 | 产出 |
|------|------|------|
| Step 1 | FastAPI 后端骨架 + 上传 + 问答接口 | 能用 Postman/curl 调通 API |
| Step 2 | 原生 HTML 前端（单页） | 浏览器可用的完整聊天界面 |
| Step 3 | 流式输出 + 证据展示 + 美化 | 完整产品体验 |

### 4.3 API 接口详细设计

```
POST /api/upload
    Content-Type: multipart/form-data
    Body: file=<binary PDF>
    Response: {
        "file_hash": "b1f7d13bc45f6f7d8862bf93ecd456ad",
        "message": "索引构建完成",
        "chunks_count": 42
    }

POST /api/chat
    Content-Type: application/json
    Body: {
        "file_hash": "b1f7d13bc45f6f7d8862bf93ecd456ad",
        "question": "这份文档讲了什么？"
    }
    Response: {
        "answer": "这份文档主要讲了...",
        "evidence": [
            {"content": "...", "score": 0.92, "page": 3},
            {"content": "...", "score": 0.87, "page": 5}
        ],
        "search_query": "这份文档讲了什么",
        "rewritten": false
    }

GET /api/health
    Response: {"status": "ok"}
```

### 4.4 前端页面草图

```
+-------------------------------------------------------------+
|  Smart-Reading PDF                                          |
+------------------------+------------------------------------+
|                        |                                    |
|  Upload PDF            |                                    |
|  +------------------+  |   Chat Area                        |
|  |  Drop or click   |  |                                    |
|  +------------------+  |   Bot: Hello, please upload...    |
|                        |                                    |
|  Uploaded Files        |   User: What's the main point?    |
|  - report.pdf (42)     |                                    |
|  - paper.pdf (28)      |   Bot: Based on the doc...        |
|                        |                                    |
|                        |   +- Evidence ------------------+  |
|                        |   | P3: "In experiments we..."  |  |
|                        |   | P5: "Furthermore..."        |  |
|                        |   +-----------------------------+  |
|                        |                                    |
+------------------------+------------------------------------+
|  [ Type your question...                        ] [Send]    |
+-------------------------------------------------------------+
```

---

## 五、与现有代码的复用关系

| 现有模块 | 复用方式 | 改动量 |
|----------|----------|--------|
| run.py -> PDFQA 类 | FastAPI 路由直接实例化调用 | 零改动 |
| config/setting.py | 直接 import | 零改动 |
| indexing/* | PDFQA._build_index() 内部调用 | 零改动 |
| querying/* | PDFQA.ask() 内部调用 | 零改动 |
| storage.py | 同上 | 零改动 |

```
  新增 web 层           现有代码（零改动）
  +----------+         +-----------------------+
  | FastAPI   |  import |  run.py (PDFQA)      |
  |  router   | ------> |    |                 |
  |           |         |    v                 |
  | /upload   |         |  config/setting.py   |
  | /chat     |         |    |                 |
  |           |         |    v                 |
  +----------+         |  indexing/*          |
                        |    |                 |
                        |    v                 |
                        |  querying/*          |
                        +-----------------------+
```

---

## 六、总结

| 维度 | 结论 |
|------|------|
| 推荐方案 | FastAPI + 原生 HTML（方案 A） |
| 新增依赖 | fastapi, uvicorn[standard], python-multipart（共 3 个） |
| 核心代码改动 | 零改动（只包装 PDFQA 类） |
| 新增代码量 | ~200 行后端 + ~300 行前端 |
| 开发时间 | 基础版 2-3 小时，完整版 4-5 小时 |
| 扩展路线 | 原生 HTML -> 加 SSE 流式 -> 可替换为 React/Vue |