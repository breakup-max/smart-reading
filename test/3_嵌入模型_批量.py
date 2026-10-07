from langchain_community.embeddings import DashScopeEmbeddings

# 创建嵌入模型对象，默认使用 text-embedding-v1
embedding_model = DashScopeEmbeddings()

# 批量处理多个文本
texts = ["猫坐在垫子上", "一只猫在垫子上休息", "今天天气很好"]
results = embedding_model.embed_documents(texts)

# 每个文本被转换成一个1536维的浮点数向量
for text, vector in zip(texts, results):
    print(f"文本：{text}")
    print(f"向量维度：{len(vector)}")
    print(f"向量前5个值：{vector}...\n")