# Graph2Seq-for-KGQG (PyTorch, uv)
Code & data for ["Toward Subgraph Guided Knowledge Graph Question Generation with Graph Neural Networks"](https://arxiv.org/abs/2004.06015).

![Model architecture.](images/arch.png)

## 环境准备（uv）
```bash
cd /path/to/Graph2Seq4TKGQG
uv venv .venv
source .venv/bin/activate
uv sync                      # 按 pyproject 安装依赖
uv pip install hatchling     # 若 build-system 需要（已装可跳过）
export PYTHONPATH=$(pwd)/src
```

## 数据与资源
- 词向量：下载 [glove.840B.300d.zip](http://nlp.stanford.edu/data/wordvecs/glove.840B.300d.zip)，解压得到 `glove.840B.300d.txt`，放到仓库 `data/`。
- 数据集：按原论文提供的数据包（OneDrive 链接）下载，放到 `data/`。
- METEOR：下载 paraphrase 资源放到 `src/core/evaluation/meteor/data/`（见 `src/core/evaluation/meteor/README.md`）。

## 训练与评测示例
训练（WebQuestions）：
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-wq/graph2seq.yml
```
训练（PQ）：
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-pq/graph2seq.yml
    ```
RL 微调（继续训练好的模型）：
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-wq/rl_graph2seq.yml
```
评测已训练模型：
```bash
PYTHONPATH=$(pwd)/src uv run python src/run_eval.py -config src/config/mhqg-wq/graph2seq.yml
    ```
输出会写入各配置的 `out_dir`。

## 常用配置参数说明（YAML）
- 数据：`trainset` / `devset` / `testset`（ndjson），`out_dir`，`pretrained`（已有模型目录）。
- 模型：`model_name`（graph2seq/seq2seq），`word_embed_dim`，`hidden_size`/`rnn_size`/`dec_hidden_size`，`rnn_type`（lstm/gru），`enc_bidi`，`kg_emb` 与 `entity_emb_dim`/`relation_emb_dim`，`enc_attn`/`dec_attn`，`pointer`，`enc_attn_cover`，`cover_loss`，`levi_graph`。
- BERT：`use_bert`，`bert_model`（如 bert-base-uncased），`finetune_bert`，`bert_layer_indexes`，`use_bert_weight`，`use_bert_gamma`。
- 训练：`batch_size`，`learning_rate`，`optimizer`，`grad_accumulated_steps`，`grad_clipping`，`word_dropout`/`rnn_dropout`/`dec_in_dropout`/`dec_out_dropout`。
- 解码：`beam_size`，`min_out_len`，`max_out_len`，`block_ngram_repeat`，`out_len_in_words`。
- 强化学习：`rl_ratio`，`rl_start_epoch`，`rl_reward_metric`，`rl_reward_metric_ratio`，`rl_wmd_ratio`，`max_wmd_reward`。

## 引用
Chen, Yu, Lingfei Wu, and Mohammed J. Zaki. "Toward Subgraph Guided Knowledge Graph Question Generation with Graph Neural Networks." arXiv preprint arXiv:2004.06015 (2020).
