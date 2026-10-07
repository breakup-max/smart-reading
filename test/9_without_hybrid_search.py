from langchain_community.embeddings import DashScopeEmbeddings
import numpy as np


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == '__main__':
    user_query = "GPT-4 参数量"

    documents = [
        "GPT-4 太贵了",
        "GPT-3 的参数规模为1750亿，参数量比较大，是当时最大的语言模型之一",
        "GPT-3.5 的参数规模为1750亿，相比GPT-3有显著提升",
        "GPT-2 的参数规模为15亿，在当时已经是非常大的模型",
        "大语言模型的参数量直接影响推理能力",
    ]

    embeddings = DashScopeEmbeddings()
    query_vector = embeddings.embed_query(user_query)
    doc_vectors = embeddings.embed_documents(documents)

    print(f"=== 查询 Q: '{user_query}' ===")
    print("-" * 65)
    for i, doc in enumerate(documents):
        sim = cosine_similarity(query_vector, doc_vectors[i])
        print(f"文档{i}: '{doc[:35]}...' 相似度: {sim:.4f}")

"""
文档3: 'GPT-2 的参数规模 为15亿，在当时已经是非常大的模型...' 相似度: 0.6114
文档2: 'GPT-3.5 的参数规模为1750亿，相比GPT-3有显著提升...' 相似度: 0.6099
文档1: 'GPT-3 的参数规模为1750亿，参数量比较大，是当时最大的语言模型...' 相似度: 0.5983
文档0: 'GPT-4 是OpenAI发布的大语言模型，拥有约1.76万亿个参数...' 相似度: 0.5820
文档4: '大语言模型的参数量直接影响推理能力...' 相似度: 0.2231
"""
