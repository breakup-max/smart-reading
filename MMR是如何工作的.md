# MMR 工作原理

参考链接：[RAG 的检索优化：MMR 平衡相关性与多样性 ](https://zhuanlan.zhihu.com/p/1893418482093257908)

## 1. 核心目标

MMR（Maximum Marginal Relevance，最大边际相关性）的目标是平衡相关性与多样性，避免检索结果过于同质化。

## 2. 底层原理

MMR 的核心计算公式如下：
$$
\text{MMR} = \arg\max_{D_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}_1(D_i, Q) - (1 - \lambda) \cdot \max_{D_j \in S} \text{Sim}_2(D_i, D_j) \right]
$$
公式参数解释：

| 参数 | 含义            | 说明                                      |
| :--- | :-------------- | :---------------------------------------- |
| Q    | 用户查询        | 输入的问题或查询文本                      |
| R    | 候选文档集      | 初始检索召回的文档集合                    |
| S    | 已选文档集      | 已经被选中作为结果的文档集合              |
| Di   | 待选文档        | 当前正在评估的候选文档                    |
| Sim1 | 查询-文档相似度 | 衡量文档与查询的相关程度                  |
| Sim2 | 文档-文档相似度 | 衡量文档与已选文档的相似程度              |
| λ    | 平衡系数        | 取值范围 [0, 1]，控制相关性与多样性的权重 |

---

公式拆解：
$$
\text{MMR} = \arg\max_{D_i \in R \setminus S} \left[ \lambda \cdot \underbrace{\text{Sim}_1(D_i, Q)}_{\text{相关性}} - (1 - \lambda) \cdot \underbrace{\max_{D_j \in S} \text{Sim}_2(D_i, D_j)}_{\text{冗余性}} \right]
$$
这个公式的核心思想就是：**相关性减去冗余性**。

- **相关性**：文档 Di 与查询 Q的匹配程度，越高越好
- **冗余性**：文档 Di 与已选文档集 S 的相似程度，越高说明信息越重复，应当扣分

当 **λ 越大**时：

- **相关性** 的权重越大
- **冗余性** 的权重越小（因为 1−λ 变小）

因此，MMR 在每一步都选择**相关性最高、但与已选文档最不重复**的文档，从而在**相关性与多样性**之间取得平衡。

## 3. MMR完整流程示例

[smart-reading/data/images/MMR示例.png ](https://gitee.com/he-wenlin/k-ai-knowledge/blob/master/smart-reading/data/images/MMR示例.png)















































