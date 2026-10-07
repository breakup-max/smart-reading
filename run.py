# run.py - PDF 问答系统（支持逐条消息，自动维护对话历史）
import os
from typing import Dict, Any, Optional

from langchain_core.chat_history import InMemoryChatMessageHistory
from config.setting import QaConfig
from indexing.indexing_pipeline import IndexingPipeline
from querying.rag_pipeline import RagPipeline


class PDFQA:
    """
    PDF 问答系统封装类，支持逐条消息交互，自动维护对话历史
    """

    def __init__(self, pdf_bytes: bytes, api_key: Optional[str] = None):
        """
        构造函数
        :param pdf_bytes: PDF 文件的二进制数据
        :param api_key: 通义千问 API Key，若为 None 则从环境变量 DASHSCOPE_API_KEY 读取
        """
        self.pdf_bytes = pdf_bytes
        # 处理 API Key
        if api_key is None:
            api_key = os.environ.get("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("未提供 API Key，且环境变量 DASHSCOPE_API_KEY 未设置")
        self.api_key = api_key

        self.cfg = QaConfig()
        self.file_hash: Optional[str] = None
        self.chat_history: Optional[InMemoryChatMessageHistory] = None
        self.rag: Optional[RagPipeline] = None

    def _build_index(self) -> None:
        """构建向量索引（内部懒加载）"""
        if self.file_hash is not None:
            return  # 已经构建过
        print("正在构建索引（首次运行会调用 Embedding API，请稍候）...")
        indexer = IndexingPipeline(self.cfg)
        self.file_hash = indexer.build_from_bytes(self.pdf_bytes, self.api_key)
        self.chat_history = InMemoryChatMessageHistory()
        self.rag = RagPipeline(self.cfg)
        print(f"索引构建完成，file_hash: {self.file_hash}")

    def ask(self, question: str) -> Dict[str, Any]:
        """
        发送一条问题，返回答案（自动维护对话历史）
        :param question: 用户问题
        :return: 包含 answer, context, evidence, search_query, rewritten 的字典
        """
        # 懒加载索引
        if self.file_hash is None:
            self._build_index()

        result = self.rag.query(
            dashscope_api_key=self.api_key,
            file_hash=self.file_hash,
            question=question,
            chat_history=self.chat_history.messages,
            enable_rewrite=True,
            enable_rerank=True,
            top_k=4,
            recall_k=30,
            hybrid_top_m=12,
        )

        # 更新对话历史
        self.chat_history.add_user_message(question)
        self.chat_history.add_ai_message(result['answer'])

        return result


def _resolve_pdf_path(input_path: str) -> str:
    if os.path.isfile(input_path):
        return input_path
    if os.path.isdir(input_path):
        pdfs = sorted(
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(".pdf")
        )
        if not pdfs:
            print(f"❌ 目录下没有 PDF 文件: {input_path}")
            return None
        if len(pdfs) == 1:
            print(f"📂 目录下只有一个 PDF，自动选用: {os.path.basename(pdfs[0])}")
            return pdfs[0]
        print(f"📂 目录下有 {len(pdfs)} 个 PDF，请选择：")
        for i, p in enumerate(pdfs, 1):
            print(f"  {i}. {os.path.basename(p)}")
        while True:
            choice = input(f"请输入编号 (1-{len(pdfs)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(pdfs):
                return pdfs[int(choice) - 1]
            print("输入无效，请重新输入")
    print(f"❌ 路径不存在: {input_path}")
    return None


def _browse_pdf() -> Optional[str]:
    import tkinter as tk
    from tkinter import filedialog
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="选择 PDF 文件",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")],
        )
        root.destroy()
        return path if path else None
    except Exception:
        return None


def _clean_path(p: str) -> str:
    p = p.strip()
    if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
        p = p[1:-1]
    p = p.replace("/", os.sep).replace("\\", os.sep)
    return p.strip()


def main():
    import sys

    if len(sys.argv) > 1:
        raw_path = _clean_path(sys.argv[1])
    else:
        raw = input("请输入 PDF 路径 ，或者（输入密码打开文件选择对话框）: ").strip()
        if raw == "wjx":
            chosen = _browse_pdf()
            if chosen:
                raw_path = chosen
            else:
                print("未选择文件，退出")
                sys.exit(1)
        else:
            raw_path = _clean_path(raw)

    pdf_path = _resolve_pdf_path(raw_path)
    if pdf_path is None:
        sys.exit(1)

    print(f"📄 加载 PDF: {pdf_path}")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    qa = PDFQA(pdf_bytes)
    qa._build_index()

    print("\n✅ 准备就绪，开始问答（输入 quit / exit 退出）\n")
    while True:
        try:
            question = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if question.lower() in ("quit", "exit", "q"):
            print("👋 再见！")
            break
        if not question:
            continue

        try:
            result = qa.ask(question)
            print(f"\nAI: {result['answer']}\n")
        except Exception as e:
            print(f"\n⚠️ 出错了: {e}\n")


if __name__ == "__main__":
    main()