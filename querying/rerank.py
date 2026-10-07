from dataclasses import dataclass
from typing import List, Tuple, Optional
import re

from langchain_community.chat_models import ChatTongyi
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config.setting import QaConfig
from querying.query_prompt import RERANK_PROMPT
from querying.vector_retriever import recall_with_scores


@dataclass
class RetrievedEvidence:
    """检索到的证据片段（经过重排序后输出的结构化信息）"""
    content: str  # 片段文本内容
    source: str  # 来源（如 PDF 文件名）
    page: Optional[int]  # 页码（如果有）
    score: float  # 最终排序分数（LLM 分数或混合分数）
    vector_score: float  # 原始向量相似度分数（0~1）
    hybrid_score: float  # 混合重排序分数（向量 + 文本重叠）
    llm_score: Optional[float] = None  # LLM 精排给出的分数（0~10）


class RerankPipeline:
    """
    完整 Rerank Pipeline：召回 → 预过滤 → Hybrid → LLM 精排
    """

    def __init__(self, config: QaConfig, llm: ChatTongyi) -> None:
        self.__config = config
        prompt = ChatPromptTemplate.from_messages([
            ("system", RERANK_PROMPT),
            ("human", "问题:{question}\n\n候选片段:\n{chunk}\n\n分数:")
        ])
        self.__llm = llm
        self.__chain = prompt | self.__llm | StrOutputParser()

    # # ------------------ 对外入口：串联整个流程 ------------------
    # def rerank(self, query: str, vectorstore: Chroma,
    #            recall_k: int = 30, hybrid_top_m: int = 12, final_top_n: int = 4) -> Tuple[List[RetrievedEvidence], str]:
    #     """
    #     完整重排序流程入口
    #     :param query: 检索查询（建议使用改写后的查询）
    #     :param vectorstore: Chroma 向量库实例
    #     :param recall_k: 向量召回的初始数量
    #     :param hybrid_top_m: 混合重排后保留的数量（送入 LLM 精排）
    #     :param final_top_n: 最终输出的证据数量
    #     :return: (evidence_list, formatted_context)
    #              evidence_list: RetrievedEvidence 列表，包含详细分数和元数据
    #              formatted_context: 格式化的上下文字符串，可直接用于 LLM 生成答案
    #     """
    #     # 1. 向量召回（带原始分数）
    #     recalled_docs, vec_scores = recall_with_scores(query, vectorstore, k=recall_k)
    #     # 2. 预过滤（去重 + 长度限制）
    #     pre_docs = self.__filter(recalled_docs)
    #     # 3. 建立原始文档内容到向量分数的映射，方便对齐
    #     score_map = {doc.page_content: s for doc, s in zip(recalled_docs, vec_scores)}
    #     aligned_vec = [score_map.get(doc.page_content, 0.5) for doc in pre_docs]
    #     # 4. 混合重排序（向量 + 文本重叠）
    #     hybrid_docs, hybrid_scores = self.__hybrid_rerank(query, pre_docs, aligned_vec, top_k=hybrid_top_m)
    #     # 5. LLM 精排
    #     final_docs, llm_scores = self.__llm_rerank(query, hybrid_docs, top_n=final_top_n)
    #     # 6.  组装证据对象（RetrievedEvidence）
    #     evidence_list = []
    #     for i, doc in enumerate(final_docs):
    #         content = doc.page_content
    #         meta = doc.metadata or {}
    #         # 查找对应的混合分数（hybrid_scores 与 hybrid_docs 顺序对应）
    #         hybrid_score = 0.0
    #         for hd, hs in zip(hybrid_docs, hybrid_scores):
    #             if hd.page_content.strip() == content:
    #                 hybrid_score = hs
    #                 break
    #         ev = RetrievedEvidence(
    #             content=doc.page_content,
    #             source=meta.get("source", "Unknown"),
    #             page=meta.get("page"),
    #             score=llm_scores[i],
    #             vector_score=score_map.get(content, 0.0),
    #             hybrid_score=hybrid_score,
    #             llm_score=llm_scores[i]
    #         )
    #         evidence_list.append(ev)
    #     # 7. 生成格式化上下文（带引用标记，供 LLM 生成答案使用）
    #     context_lines = []
    #     for idx, ev in enumerate(evidence_list, 1):
    #         page_str = f"第{ev.page}页" if ev.page else "未知页"
    #         # 序号，来源:哪个PDF，哪一页，哪段内容
    #         context_lines.append(f"[证据{idx} | 来源：{ev.source} | {page_str}]\n{ev.content}")
    #     context = "\n\n".join(context_lines)
    #
    #     return evidence_list, context

    def rerank(
            self,
            query: str,
            recalled_docs: List[Document],
            vec_scores: List[float],
            hybrid_top_m: int = 12,
            final_top_n: int = 4
    ) -> Tuple[List[RetrievedEvidence], str]:
        """
        重排序流程入口（不再包含向量召回）
        :param query: 检索查询
        :param recalled_docs: 已召回的文档列表
        :param vec_scores: 对应的向量分数列表
        :param hybrid_top_m: 混合重排后保留的数量
        :param final_top_n: 最终输出的证据数量
        :return: (evidence_list, formatted_context)
        """
        # 预过滤
        pre_docs = self.__filter(recalled_docs)
        # 对齐向量分数（因为过滤后可能减少）
        score_map = {doc.page_content: s for doc, s in zip(recalled_docs, vec_scores)}
        aligned_vec = [score_map.get(doc.page_content, 0.5) for doc in pre_docs]

        # 混合重排
        hybrid_docs, hybrid_scores = self.__hybrid_rerank(query, pre_docs, aligned_vec, top_k=hybrid_top_m)

        # LLM 精排
        final_docs, llm_scores = self.__llm_rerank(query, hybrid_docs, top_n=final_top_n)

        # 组装证据
        evidence_list = []
        for i, doc in enumerate(final_docs):
            content = doc.page_content
            meta = doc.metadata or {}
            hybrid_score = 0.0
            for hd, hs in zip(hybrid_docs, hybrid_scores):
                if hd.page_content.strip() == content:
                    hybrid_score = hs
                    break
            ev = RetrievedEvidence(
                content=doc.page_content,
                source=meta.get("source", "Unknown"),
                page=meta.get("page"),
                score=llm_scores[i],
                vector_score=score_map.get(content, 0.0),
                hybrid_score=hybrid_score,
                llm_score=llm_scores[i]
            )
            evidence_list.append(ev)

        # 格式化上下文
        context_lines = []
        for idx, ev in enumerate(evidence_list, 1):
            page_str = f"第{ev.page + 1}页" if ev.page is not None else "未知页"
            context_lines.append(f"[证据{idx} | 来源：{ev.source} | {page_str}]\n{ev.content}")
        context = "\n\n".join(context_lines)

        return evidence_list, context

    # ------------------ 预过滤： 长度过滤+ 去重 ------------------
    def __filter(self, docs: List[Document], min_len: int = 40, max_len: int = 2000) -> List[Document]:
        """
        过滤掉过短（<min_len）或过长（>max_len）的片段，并去重
        :param docs: 原始文档列表
        :param min_len: 最小字符数
        :param max_len: 最大字符数
        :return: 过滤后的文档列表
        """
        # 基于长度过滤
        filtered = []
        for doc in docs:
            text = doc.page_content
            if min_len <= len(text) <= max_len:
                filtered.append(doc)

        # 基于 page_content 去重，保留第一次出现的文档
        is_contains = set()
        kept = []
        for doc in filtered:
            key = doc.page_content
            if key not in is_contains:
                is_contains.add(key)
                kept.append(doc)
        return kept

    # ------------------ 混合重排：向量分数 + 文本重叠分数 ------------------
    def __hybrid_rerank(self, question: str, documents: List[Document],
                        vector_scores: List[float], top_k: int = 12) -> Tuple[List[Document], List[float]]:
        """
        混合重排序：结合向量分数和文本重叠分数，并加入长度/关键词规则
        :param question: 用户问题（用于计算重叠和关键词）
        :param documents: 待重排的文档列表
        :param vector_scores: 对应的向量分数列表
        :param top_k: 保留前 top_k 个
        :return: (排序后的文档列表, 对应的混合分数列表)
        """
        if not documents:
            return [], []
        # 计算每个文档的文本重叠分数
        overlap_scores = [self.__simple_overlap_score(question, doc.page_content) for doc in documents]

        final = []  # 存储 (原始索引, 混合分数)
        for i, (vector_score, overlap_score) in enumerate(zip(vector_scores, overlap_scores)):
            # 混合分数 = 0.3 * 向量分 + 0.7 * 文本重叠分
            hybrid = 0.3 * vector_score + 0.7 * overlap_score
            text = documents[i].page_content
            # 长度规则：果断或过长降权
            if len(text) < 80:
                hybrid *= 0.8
            elif len(text) > 1600:
                hybrid *= 0.9
            # 关键词规则：如果问题和文本有共同单词，适当提权
            if set(question.lower().split()) & set(text.lower().split()):
                hybrid *= 1.1
            final.append((i, hybrid))
        # 按照混合分数降序排序
        final.sort(key=lambda t: t[1], reverse=True)
        idx_sorted = [i for i, _ in final[:top_k]]
        docs_sorted = [documents[i] for i in idx_sorted]
        scores_sorted = [final[i][1] for i in range(top_k) if i < len(final)]
        return docs_sorted, scores_sorted

    def __simple_overlap_score(self, query: str, text: str) -> float:
        """
        计算查询与文本的 Jaccard 重叠度（支持中文双字词 + 英文单词）
        :param query: 查询字符串
        :param text: 文本片段
        :return: 重叠度，范围 [0,1]
        """

        def tokens(s: str):
            s = s.lower()
            # 提取连续的中文字符（至少两个）
            chinese = re.findall(r'[\u4e00-\u9fff]{2,}', s)
            # 提取英文单词
            english = re.findall(r'[a-z]+', s)
            # 对中文生成双字 bigram
            bigrams = [ch[i:i + 2] for ch in chinese for i in range(len(ch) - 1)]
            return set(bigrams + english)

        q_tokens = tokens(query)
        t_tokens = tokens(text)
        if not q_tokens:
            return 0.0
        inter = q_tokens & t_tokens
        union = q_tokens | t_tokens
        return len(inter) / len(union) if union else 0.0

    # ------------------ LLM 精排：使用大模型打分 ------------------
    def __llm_rerank(self, question: str, documents: List[Document], top_n: int = 4) -> Tuple[
        List[Document], List[float]]:
        """
        利用 LLM 对每个候选片段进行 0-10 的打分，并按分数排序取前 top_n
        :param question: 用户问题
        :param documents: 待精排的文档列表
        :param top_n: 最终保留的文档数量
        :return: (排序后的文档列表, LLM 分数列表)
        """
        if not documents:
            return [], []
        scored = []
        for doc in documents:
            score_text = self.__chain.invoke({"question": question, "chunk": doc.page_content})
            # 从 LLM 返回结果中提取数字（可能带小数点）
            try:
                match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                score = float(match.group(1)) if match else 0.0
            except Exception:
                score = 0.0
            scored.append((score, doc))
        # 按分数降序排序
        scored.sort(key=lambda x: x[0], reverse=True)
        docs = [d for _, d in scored[:top_n]]
        scores = [s for s, _ in scored[:top_n]]
        return docs, scores
