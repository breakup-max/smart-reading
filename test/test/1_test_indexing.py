from config.setting import QaConfig
from indexing.indexing_pipeline import IndexingPipeline

cfg = QaConfig()
pipeline = IndexingPipeline(cfg)

# 从文件构建
pdf_file_path = "E:\python\k-ai-knowledge\smart-reading\data\sample_document.pdf"
file_hash = pipeline.build_from_file(pdf_file_path, "sk-339cd4d2e1f9426e8d08c766415363a2")
print(f"索引构建完成，file_hash: {file_hash}")