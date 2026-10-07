from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import numpy as np


def cosine_similarity(a, b):
    """计算余弦相似度"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == '__main__':
    # 1. 准备文档数据
    documents = [
        "学习AI需要先掌握线性代数、概率论和微积分，这是算法的基础",
        "人工智能的核心数学知识包括矩阵运算、概率统计和导数计算",
        "Python是AI开发的首选语言，需要熟悉numpy、pandas等数据处理库",
        "通过Kaggle竞赛实战，从泰坦尼克号预测等项目开始练手",
        "推荐李飞飞的CS231n课程和《深度学习》花书，系统学习理论",
        "如何做红烧肉，需要准备五花肉、冰糖和生抽",
    ]

    # 转换为 Document 对象
    data = [Document(page_content=doc) for doc in documents]

    # 2. 创建 Chroma 客户端并存入文档（显式指定余弦相似度）
    chroma_db = Chroma(
        collection_name="ai_learning",
        embedding_function=DashScopeEmbeddings(),
        persist_directory="./chroma_db",
        collection_metadata={"hnsw:space": "cosine"}  # 指定使用余弦相似度
    )

    # 添加文档
    chroma_db.add_documents(
        documents=data,
        ids=[f"id-{i}" for i in range(len(data))]
    )
    print("文档已存入 Chroma 数据库")
    print("-" * 65)

    # 3. 用户查询
    user_query = "如何学习人工智能？"

    # 4. 普通相似度检索（k=3）
    print(f"=== 查询 Q: '{user_query}' ===")
    print("\n【普通相似度检索 results】")
    results = chroma_db.similarity_search_with_relevance_scores(user_query, k=3)

    for i, (doc, score) in enumerate(results):
        print(f"排名{i + 1}: 相似度={score:.4f} | 内容: {doc.page_content[:40]}...")

    print("\n" + "=" * 65)

    # 5. MMR 检索（k=3，fetch_k=5）
    print("\n【MMR 检索 results】")
    mmr_results = chroma_db.max_marginal_relevance_search(
        query=user_query,
        k=3,  # 最终返回 3 个
        fetch_k=5,  # 候选池 5 个
        lambda_mult=0.6  # 平衡参数
    )

    for i, doc in enumerate(mmr_results):
        print(f"排名{i + 1}: 内容: {doc.page_content[:40]}...")