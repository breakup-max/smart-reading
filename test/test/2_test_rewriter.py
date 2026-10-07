from langchain_community.chat_models import ChatTongyi
from langchain_core.chat_history import InMemoryChatMessageHistory
from querying.rewrite import QueryRewriter

llm = ChatTongyi(model="qwen3-max")
rewriter = QueryRewriter(llm)

history = InMemoryChatMessageHistory()
history.add_user_message("我之前问过那篇关于注意力机制的论文")
history.add_ai_message("是的，那篇论文是《Attention Is All You Need》")

question = "那篇论文的核心贡献是什么？"
rewritten = rewriter.rewrite(question, history.messages)
print(f"原始问题: {question}")
print(f"改写后: {rewritten}")