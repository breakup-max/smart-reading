from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

if __name__ == '__main__':
    # 用户查询
    user_query = "如何学习人工智能？"

    # 向量数据库中存储的文本内容
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

    # 创建 Chroma 客户端并存入文档
    chroma_db = Chroma(
        collection_name="ai_learning",
        embedding_function=DashScopeEmbeddings(),
        persist_directory="./chroma_db",
        collection_metadata={"hnsw:space": "cosine"}
    )

    # 添加文档
    chroma_db.add_documents(
        documents=data,
        ids=[f"id-{i}" for i in range(len(data))]
    )

    # 计算查询与各文本的相似度（使用 Chroma 检索）
    print(f"=== 查询 Q: '{user_query}' ===")
    print("-" * 65)

    # 获取所有文档及其相似度
    results = chroma_db.similarity_search_with_relevance_scores(user_query, k=len(documents))

    for i, (doc, score) in enumerate(results):
        print(f"文档{i}: '{doc.page_content[:30]}...' 相似度: {score:.4f}")