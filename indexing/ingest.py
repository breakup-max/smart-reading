# indexing/ingest.py
# 职责：PDF 文档加载 + 切分成文本块（chunks）
# 说明：
# - 切分粒度决定检索召回质量（太粗则噪音多，太细则丢失上下文）
# - chunk_overlap 可以减少边界信息丢失（如跨页句子被切断）
# - 中文场景优先按句号、感叹号等标点切分，避免切断完整句子

from config.setting import QaConfig
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import tempfile
import os

class PdfIngestor:
    """PDF 文档加载与切分器"""
    def __init__(self, config: QaConfig) -> None:
        self.__config = config

    def ingest(self, pdf_bytes: bytes) -> List[Document]:
        """
        从 PDF 字节数据 → 加载 → 切分 → 返回 chunks
        :param pdf_bytes: PDF 文件的原始字节流（由 storage.py 的 load() 获取）
        :return: 切分后的 Document 列表，可直接用于向量化
        """
        # 创建临时文件（因为 PyMuPDFLoader 需要文件路径）
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            tmp_path = tmp.name
        try:
            # 加载 PDF（每页一个 Document）
            documents = self.load(tmp_path)
            # 切分成 chunks
            return self.split(documents)
        finally:
            # 清理临时文件
            os.unlink(tmp_path)

    def load(self, pdf_path: str) -> List[Document]:
        """
        加载 PDF 文件，每页生成一个 Document 对象
        :param pdf_path: PDF 文件路径（由 storage.py 生成的临时文件）
        :return: Document 列表，每个 Document 包含 page_content 和 metadata（如页码、来源）
        """
        return PyMuPDFLoader(pdf_path).load()

    def split(self, docs):
        """
        将每个页面的 Document 切分成更小的文本块（chunk）
        切分策略：
        - 优先按中文句号、感叹号、问号、分号、逗号等切分
        - 如果 chunk 仍然超过 chunk_size，则递归按空格/换行切分
        - 保留 chunk_overlap 个字符的重叠，避免语义断裂
        :param docs: 原始 Document 列表（每页一个）
        :return: 切分后的 Document 列表（每个 chunk 一个）
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.__config.chunk_size,
            chunk_overlap=self.__config.chunk_overlap,
            is_separator_regex=True,      # 启用正则分隔符
            separators=["(?<=。)", "(?<=！)", "(?<=？)", "(?<=；)", "(?<=，)", " ", "\n"],
        )
        return splitter.split_documents(docs)