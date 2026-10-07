import os
from typing import List

from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document

from config.setting import QaConfig


class VectorStoreManager:
    """向量库管理器：负责加载已有库或新建库"""
    def __init__(self, config: QaConfig, embeddings: DashScopeEmbeddings):
        """
        初始化管理器
        :param cfg: 全局配置（包含 chroma_root_dir）
        :param embeddings: Embedding 模型实例（已绑定 API Key）
        """
        self.__config = config
        self._embeddings = embeddings

    def load_or_build(self, file_hash: str, chunks: List[Document] = None) -> Chroma:
        """
        加载已有向量库，如果不存在则用 chunks 新建
        :param file_hash: PDF 文件的 MD5 哈希
        :param chunks: 切分后的 Document 列表（新建时必须提供）
        :return: Chroma 向量库实例
        """
        persist_dir = os.path.join(self.__config.chroma_root_dir, f"pdf_{file_hash}")
        collection_name = f"pdf_qa_{file_hash}"

        # 尝试加载已有向量库
        store = Chroma(
            collection_name=collection_name,
            embedding_function=self._embeddings,
            persist_directory=persist_dir,
            collection_metadata={"hnsw:space": "cosine"}  # 余弦相似度
        )

        # 检查是否已经有了数据，有数据就直接返回 store
        if store._collection.count() > 0:
            return store

        # 无数据且未提供 chunks，则报错
        if not chunks:
            raise ValueError("向量库不存在且未提供 chunks，无法建库")
        # 存储数据
        store.add_documents(
            documents=chunks,
            ids=[f"id-{idx}" for idx in range(1, len(chunks) + 1)],
        )

        return store
