from langchain_text_splitters import RecursiveCharacterTextSplitter

text = """春秋战国时期是中国历史上思想文化最为繁荣的时代。诸子百家争鸣，儒家、道家、墨家、法家等学派相继兴起。孔子周游列国，宣扬仁义礼智信的思想。老子著《道德经》，阐述无为而治的哲学理念。

秦始皇统一六国后，推行书同文、车同轨、统一度量衡等政策。焚书坑儒虽然巩固了中央集权，但也造成了文化的巨大损失。万里长城的修建抵御了北方游牧民族的侵扰，成为中华民族的象征之一。

唐朝是中国封建社会的鼎盛时期。贞观之治、开元盛世使国力达到顶峰。李白、杜甫等诗人的作品流传千古。丝绸之路的畅通促进了中外经济文化交流。长安城成为当时世界上最大的国际化都市。"""

splitter = RecursiveCharacterTextSplitter(
    chunk_size=55,
    chunk_overlap=8,
    separators=["\n\n", "\n", "。", "，", "、", " ", ""],
    length_function=len,
    keep_separator=True  # 分隔符保留在末尾
)

chunks = splitter.split_text(text)
for i, chunk in enumerate(chunks):
    print(f"--- 块 {i+1} (长度: {len(chunk)}) ---")
    print(chunk)
    print()