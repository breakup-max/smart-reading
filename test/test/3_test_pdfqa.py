import os
import sys
from run import PDFQA

pdf_path = "E:\python\k-ai-knowledge\smart-reading\data\sample_document.pdf"
if not os.path.exists(pdf_path):
    print("请提供 sample.pdf")
    sys.exit()

with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

qa = PDFQA(pdf_bytes, api_key=None)   # 使用环境变量中的 key

# 模拟逐条发送
q1 = "GPT-3的论文链接是什么？"
r1 = qa.ask(q1)
print(f"Q: {q1}\nA: {r1['answer']}\n")

q2 = "它的Transformer层数有多少层？"   # 这里的“它”依赖上一轮历史
r2 = qa.ask(q2)
print(f"Q: {q2}\nA: {r2['answer']}\n")