from langchain_community.embeddings import DashScopeEmbeddings

# 创建模型对象，默认使用 text-embedding-v1
embedding_model = DashScopeEmbeddings()

user_input = "猫坐在垫子上"
result = embedding_model.embed_query(user_input)
print(type(result))  # <class 'list'>
print(len(result))  # 1536
print(result)  # 输出一个包含1536个浮点数的向量列表
