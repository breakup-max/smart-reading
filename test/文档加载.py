from langchain_community.document_loaders import PyMuPDFLoader

file_path = "E:\python\k-ai-knowledge\smart-reading\data\sample_document.pdf"

docs = PyMuPDFLoader(file_path).load()
print(type(docs))  # <class 'list'>
print(len(docs))  # 6
print(type(docs[0]))  # <class 'langchain_core.documents.base.Document'>

for doc in docs:
    print(doc)
"""
1. 每个元素是一个 <class 'langchain_core.documents.base.Document'> 对象
2. 每个对象里面有page_content和metadata元信息，page_content是文档的内容，metadata是元信息
3. 每一个Document是pdf的一页内容
"""
