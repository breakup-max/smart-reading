from typing import List, Dict, Any
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma

from config.setting import QaConfig
from indexing.vectorstore import VectorStoreManager
from querying.rewrite import QueryRewriter
from querying.rerank import RerankPipeline, RetrievedEvidence
from querying.answer import AnswerGenerator
from querying.vector_retriever import recall_with_scores   # 导入向量召回函数


class RagPipeline:
    """RAG 在线问答流水线（只负责查询，不负责索引构建）"""
    def __init__(self, config: QaConfig):
        self.cfg = config
        self._llm = None
        self._embeddings = None

    def _init_llm(self, api_key: str) -> ChatTongyi:
        if self._llm is None:
            self._llm = ChatTongyi(model="qwen3-max", api_key=api_key)
        return self._llm

    def _init_embeddings(self, api_key: str) -> DashScopeEmbeddings:
        if self._embeddings is None:
            self._embeddings = DashScopeEmbeddings(
                model=self.cfg.embedding_model,
                dashscope_api_key=api_key
            )
        return self._embeddings

    def _load_vectorstore(self, file_hash: str, api_key: str) -> Chroma:
        embeddings = self._init_embeddings(api_key)
        manager = VectorStoreManager(self.cfg, embeddings)
        return manager.load_or_build(file_hash)

    def query(
        self,
        dashscope_api_key: str,
        file_hash: str,
        question: str,
        chat_history,
        *,
        top_k: int = 4,
        enable_rewrite: bool = True,
        enable_rerank: bool = True,
        recall_k: int = 30,
        hybrid_top_m: int = 12,
    ) -> Dict[str, Any]:
        llm = self._init_llm(dashscope_api_key)
        vectorstore = self._load_vectorstore(file_hash, dashscope_api_key)

        # 查询改写
        search_query = question
        if enable_rewrite:
            rewriter = QueryRewriter(llm)
            messages = chat_history
            search_query = rewriter.rewrite(question, messages)

        evidence_list: List[RetrievedEvidence] = []
        context = ""

        if enable_rerank:
            # 向量召回（从 rerank 中移出）
            recalled_docs, vec_scores = recall_with_scores(search_query, vectorstore, k=recall_k)
            # 重排序
            rerank_pipeline = RerankPipeline(self.cfg, llm)
            evidence_list, context = rerank_pipeline.rerank(
                query=search_query,
                recalled_docs=recalled_docs,
                vec_scores=vec_scores,
                hybrid_top_m=hybrid_top_m,
                final_top_n=top_k,
            )
        else:
            # 简单检索
            docs = vectorstore.similarity_search(search_query, k=top_k)
            context = "\n\n".join([doc.page_content for doc in docs])

        # 生成答案
        answer_gen = AnswerGenerator(llm)
        answer = answer_gen.generate(search_query, chat_history, context)

        return {
            "answer": answer,
            "context": context,
            "evidence": evidence_list,
            "search_query": search_query,
            "rewritten": enable_rewrite and (search_query != question),
        }