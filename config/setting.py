# config.py：集中管理所有可调参数

from dataclasses import dataclass


# Qa 是 Q&A（Question and Answer，问答）的变体写法，通常写作 QA。
@dataclass(frozen=True)
class QaConfig:
    # 1.大模型相关参数
    # 1.1.通义千问模型版本
    llm_model: str = "qwen3-max"
    # 1.2.温度参数 0~1，越低越保守
    llm_temperature: float = 0.2

    # 2. Embedding 配置
    # 2.1 嵌入模型参数
    embedding_model: str = "text-embedding-v1"
    # 2.2. chunk大小（字符数）
    chunk_size: int = 800
    # 2.3. chunk重叠（字符数）
    chunk_overlap: int = 120

    # 3.送入 LLM 的上下文最大长度
    context_max_chars: int = 1400

    # 4.Chroma 持久化根目录的位置
    chroma_root_dir: str = ".chroma"
