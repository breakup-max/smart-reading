# querying/rewrite.py
# 职责：查询改写，替换掉一些指代词
from typing import List

from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from querying.query_prompt import REWRITE_PROMPT


class QueryRewriter:
    """查询改写器：把用户问题改写成可独立检索的查询"""

    def __init__(self, llm: ChatTongyi) -> None:
        self.__prompt = ChatPromptTemplate.from_messages([
            ("system", REWRITE_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "原始问题：{question}\n请改为独立检索查询:")
        ])
        self.__llm = llm

    def rewrite(self, question: str, chat_history: List[BaseMessage]) -> str:
        # 代码健壮性判断（判断）
        q = (question or "").strip()
        if not q:
            return q

        # 短问题或者没有指代的问题，直接跳过。[个人觉得没啥必要，还是让AI去判断~]
        if len(q) < 10 or not any(kw in q for kw in ["那篇", "刚才", "它", "这个", "该"]):
            return q

        # query rewrite逻辑
        try:
            chain = self.__prompt | self.__llm | StrOutputParser()
            rewrite = chain.invoke(input={"question": q, "chat_history": chat_history})
            return rewrite
        except Exception:
            return q
