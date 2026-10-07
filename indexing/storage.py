# storage.py
# 职责：负责把上传的 PDF 字节流落盘成临时文件，并计算文件哈希（MD5）
# 说明：
# - LangChain 的 PyMuPDFLoader 需要文件路径，不能直接使用字节流
# - 不同请求/不同文件用 file_hash 命名，避免覆盖
# - 同一份 PDF 多次上传时，哈希相同，可用于判断向量库是否已存在
import hashlib
import os


class PdfBytesStore:
    def store(self, pdf_bytes: bytes, file_hash: str) -> str:
        """
        将 PDF 字节保存为临时文件
        :param pdf_bytes: PDF 的原始字节数据
        :param file_hash: 文件内容的 MD5 哈希值（用于命名）
        :return: 临时文件的路径
        """
        temp_path = f"temp_{file_hash}.pdf"
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)
        return temp_path

    def compute_hash(self, pdf_bytes: bytes) -> str:
        return hashlib.md5(pdf_bytes).hexdigest()