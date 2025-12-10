# Graph2Seq-for-KGQG (PyTorch, uv)
Code and data for [“Toward Subgraph Guided Knowledge Graph Question Generation with Graph Neural Networks”](https://arxiv.org/abs/2004.06015).

![Model architecture.]

## Environment (uv)
```bash
cd /path/to/Graph2Seq4TKGQG
uv venv .venv
source .venv/bin/activate
uv sync                  # install dependencies from pyproject
uv pip install hatchling # only if build-system requires
export PYTHONPATH=$(pwd)/src
```

## Data and resources
- Word vectors: download [glove.840B.300d.zip](http://nlp.stanford.edu/data/wordvecs/glove.840B.300d.zip), extract `glove.840B.300d.txt` into `data/`.
- Datasets: place the benchmark data (e.g., mhqg-wq, mhqg-pq, or converted MULTITQ) under `data/`.
- METEOR: download `paraphrase-en.gz` into `src/core/evaluation/meteor/data/` (see `src/core/evaluation/meteor/README.md`).

## Run examples
Train (WebQuestions):
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-wq/graph2seq.yml
```
Train (PQ):
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-pq/graph2seq.yml
```
RL finetune:
```bash
PYTHONPATH=$(pwd)/src uv run python src/main.py -config src/config/mhqg-wq/rl_graph2seq.yml
```
Evaluate:
```bash
PYTHONPATH=$(pwd)/src uv run python src/run_eval.py -config src/config/mhqg-wq/graph2seq.yml
```
Outputs are written to the `out_dir` specified in each config.

## Config highlights (YAML)
- Data: `trainset` / `devset` / `testset` (JSONL), `out_dir`, `pretrained`.
- Model: `model_name` (graph2seq/seq2seq), `word_embed_dim`, `hidden_size` / `rnn_size` / `dec_hidden_size`, `rnn_type` (lstm/gru), `enc_bidi`, `kg_emb`, `entity_emb_dim` / `relation_emb_dim`, `enc_attn` / `dec_attn`, `pointer`, `enc_attn_cover`, `cover_loss`, `levi_graph`.
- BERT: `use_bert`, `bert_model`, `finetune_bert`, `bert_layer_indexes`, `use_bert_weight`, `use_bert_gamma`.
- Training: `batch_size`, `learning_rate`, `optimizer`, `grad_accumulated_steps`, `grad_clipping`, `word_dropout` / `rnn_dropout` / `dec_in_dropout` / `dec_out_dropout`.
- Decoding: `beam_size`, `min_out_len`, `max_out_len`, `block_ngram_repeat`, `out_len_in_words`.
- RL: `rl_ratio`, `rl_start_epoch`, `rl_reward_metric`, `rl_reward_metric_ratio`, `rl_wmd_ratio`, `max_wmd_reward`.

## Citation
Chen, Yu, Lingfei Wu, and Mohammed J. Zaki. “Toward Subgraph Guided Knowledge Graph Question Generation with Graph Neural Networks.” arXiv preprint arXiv:2004.06015 (2020).
