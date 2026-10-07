from langchain_community.embeddings import DashScopeEmbeddings
import numpy as np


def cosine_similarity(a, b):
    """计算余弦相似度"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == '__main__':
    # 准备三个测试文本：前两个语义相近，第三个语义无关
    texts = ["猫坐在垫子上", "一只猫在垫子上休息", "今天天气很好"]
    vectors = DashScopeEmbeddings().embed_documents(texts)

    # 计算相似度并观察结果
    print(f"'{texts[0]}' 与 '{texts[1]}' 的相似度: {cosine_similarity(vectors[0], vectors[1])}")
    print(f"'{texts[0]}' 与 '{texts[2]}' 的相似度: {cosine_similarity(vectors[0], vectors[2])}")
    print(f"'{texts[1]}' 与 '{texts[2]}' 的相似度: {cosine_similarity(vectors[1], vectors[2])}")
