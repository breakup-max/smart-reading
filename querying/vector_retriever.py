from typing import List, Tuple
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

def recall_with_scores(
    query: str,
    vectorstore: Chroma,
    k: int = 30
) -> Tuple[List[Document], List[float]]:
    """
    使用向量检索召回 k 个最相似的文档，并返回相关性分数（0~1，越高越相似）
    参数:
        query: 改写后的用户查询字符串
        vectorstore: Chroma 向量数据库实例
        k: 召回数量，默认 30
    返回:
        (docs, scores): 文档列表和对应的分数列表
    """
    # similarity_search_with_relevance_scores 返回 List[Tuple[Document, float]]
    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)

    docs = []
    scores = []
    for doc, score in results:
        # 直接使用原有的 Document 对象，无需重新创建
        doc.page_content = doc.page_content.strip()
        docs.append(doc)
        scores.append(score)

    return docs, scores