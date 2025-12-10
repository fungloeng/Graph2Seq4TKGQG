# 数据集说明文档

本文档介绍 Graph2Seq-for-KGQG 项目使用的数据集格式和结构。

## 概述

项目支持两个主要数据集：
- **mhqg-wq**: 基于 WebQuestions/ComplexWebQuestions 的多跳问题生成数据集
- **mhqg-pq**: 基于 PathQuestions 的路径问题生成数据集

## 数据格式

### 文件格式

所有数据集文件采用 **JSON Lines** 格式（`.json`），每行一个 JSON 对象，对应一个训练/测试样本。

### JSON 数据结构

每个样本包含以下字段：

```json
{
  "inGraph": {
    "g_node_names": {
      "entity_id_1": "entity name 1",
      "entity_id_2": "entity name 2",
      ...
    },
    "g_node_types": {
      "entity_id_1": "type/path/to/entity",
      ...
    },
    "g_edge_types": {
      "edge_id_1": "relation/path/to/relation",
      "edge_id_2": "relation/path/to/relation",
      ...
    },
    "g_adj": {
      "entity_id_1": {
        "entity_id_2": "edge_id_1" 或 ["edge_id_1", "edge_id_2", ...],
        ...
      },
      ...
    }
  },
  "outSeq": "what is the question text?",
  "answers": ["answer1", "answer2", ...],
  "topicEntityID": "entity_id_1",
  "answer_ids": ["entity_id_2", "entity_id_3"]
}
```

### 字段说明

#### `inGraph` (输入子图)

- **`g_node_names`** (必需): 字典，键为实体ID，值为实体名称（字符串）
  - 示例: `{"m.01_234": "Barack Obama", "m.02_567": "United States"}`

- **`g_node_types`** (可选): 字典，键为实体ID，值为实体类型路径
  - 示例: `{"m.01_234": "people/person"}`

- **`g_edge_types`** (必需): 字典，键为边ID，值为关系类型路径
  - 示例: `{"r.01": "people/person/place_of_birth"}`

- **`g_adj`** (必需): 邻接表，表示图的连接关系
  - 格式: `{源实体ID: {目标实体ID: 边ID或边ID列表}}`
  - 示例: `{"m.01_234": {"m.02_567": "r.01"}}` 表示从实体1到实体2有一条边r.01
  - 支持多重边：`{"m.01_234": {"m.02_567": ["r.01", "r.02"]}}`

#### `outSeq` (输出序列)

- **类型**: 字符串
- **内容**: 生成的问题文本
- **示例**: `"who was born in the united states?"`

#### `answers` (答案列表)

- **类型**: 字符串列表
- **内容**: 问题的标准答案（可能有多个）
- **示例**: `["Barack Obama", "George Washington"]`

#### `topicEntityID` (可选)

- **类型**: 字符串
- **内容**: 主题实体ID，用于标识问题的核心实体
- **示例**: `"m.01_234"`

#### `answer_ids` (可选)

- **类型**: 字符串列表
- **内容**: 答案对应的实体ID列表
- **示例**: `["m.01_234", "m.03_456"]`

## 数据集详情

### mhqg-wq (WebQuestions)

**来源**: 基于 ComplexWebQuestions 数据集，使用 Freebase 知识图谱

**特点**:
- 多跳复杂问题
- 支持实体和关系的预训练嵌入（`entity_emb.ndjson`, `relation_emb.ndjson`）
- 包含更丰富的实体类型信息
- 数据规模：训练集约 18,989 条，验证集和测试集各约 2,000 条

**文件位置**:
```
data/mhqg-wq/
├── train.json          # 训练集
├── dev.json            # 验证集
├── test.json           # 测试集
├── vocab_model_min3    # 词表模型（最小词频3）
└── (可选) entity_emb.ndjson      # 实体嵌入
└── (可选) relation_emb.ndjson   # 关系嵌入
```

**配置示例**:
```yaml
dataset_name: 'mhqg-wq'
trainset: 'data/mhqg-wq/train.json'
devset: 'data/mhqg-wq/dev.json'
testset: 'data/mhqg-wq/test.json'
saved_vocab_file: 'data/mhqg-wq/vocab_model_min3'
```

### mhqg-pq (PathQuestions)

**来源**: 基于 PathQuestions 数据集

**特点**:
- 路径式问题（通常为单跳或简单多跳）
- 图结构相对简单
- 数据规模：通常比 mhqg-wq 小

**文件位置**:
```
data/mhqg-pq/
├── train.json          # 训练集
├── dev.json            # 验证集
├── test.json           # 测试集
└── vocab_model_min3    # 词表模型（最小词频3）
```

**配置示例**:
```yaml
dataset_name: 'mhqg-pq'
trainset: 'data/mhqg-pq/train.json'
devset: 'data/mhqg-pq/dev.json'
testset: 'data/mhqg-pq/test.json'
saved_vocab_file: 'data/mhqg-pq/vocab_model_min3'
```

## 数据预处理

### Levi 图转换

代码支持 **Levi 图转换**（默认启用），将边视为节点：
- 原始图: `节点1 --边1--> 节点2`
- Levi 图: `节点1 --边1--> 虚拟节点(边1) --边2--> 节点2`

这有助于模型更好地处理边信息。

### 答案匹配标记

代码会自动为每个节点生成答案匹配标记（`g_node_ans_match`）：
- `1`: 该节点是答案节点
- `2`: 该节点不是答案节点

## 数据示例

### mhqg-wq 示例

```json
{
  "inGraph": {
    "g_node_names": {
      "m.01_234": "Barack Obama",
      "m.02_567": "United States",
      "m.03_890": "Hawaii"
    },
    "g_edge_types": {
      "r.01": "people/person/place_of_birth",
      "r.02": "location/location/containedby"
    },
    "g_adj": {
      "m.01_234": {
        "m.02_567": "r.01"
      },
      "m.02_567": {
        "m.03_890": "r.02"
      }
    }
  },
  "outSeq": "who was born in a state that is contained by the united states?",
  "answers": ["Barack Obama"],
  "topicEntityID": "m.01_234",
  "answer_ids": ["m.01_234"]
}
```

### mhqg-pq 示例

```json
{
  "inGraph": {
    "g_node_names": {
      "entity_1": "person",
      "entity_2": "country",
      "entity_3": "city"
    },
    "g_edge_types": {
      "rel_1": "born_in",
      "rel_2": "located_in"
    },
    "g_adj": {
      "entity_1": {
        "entity_3": "rel_1"
      },
      "entity_3": {
        "entity_2": "rel_2"
      }
    }
  },
  "outSeq": "which person was born in a city located in which country?",
  "answers": ["person"]
}
```

## 数据准备脚本

项目提供了数据准备脚本（位于 `src/scripts/`）：

- `prepare_mhqg_wq.py`: 准备 WebQuestions 数据
- `prepare_mhqg_pq.py`: 准备 PathQuestions 数据
- `prepare_freebase_for_webquestions.py`: 处理 Freebase 知识图谱

## 词表文件

每个数据集都有对应的词表文件（`vocab_model_min3`），包含：
- 词表（最小词频为3）
- 节点词汇表（如果使用 KG 嵌入）
- 边类型词汇表（如果使用 KG 嵌入）

词表在首次运行时自动生成，后续训练会复用。

## 注意事项

1. **数据路径**: 确保所有数据文件路径在配置文件中正确设置（相对于项目根目录）
2. **JSON 格式**: 每行必须是有效的 JSON 对象，不能有多余的逗号或格式错误
3. **图结构**: `g_adj` 必须非空，至少包含一条边
4. **答案匹配**: 如果提供了 `answer_ids`，会优先使用；否则会根据 `answers` 文本匹配节点名称
5. **编码**: 建议使用 UTF-8 编码保存 JSON 文件

## 引用

如果使用这些数据集，请引用原始论文：

```bibtex
@article{chen2020toward,
  title={Toward Subgraph Guided Knowledge Graph Question Generation with Graph Neural Networks},
  author={Chen, Yu and Wu, Lingfei and Zaki, Mohammed J.},
  journal={arXiv preprint arXiv:2004.06015},
  year={2020}
}
```

