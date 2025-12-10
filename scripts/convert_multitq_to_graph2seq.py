import argparse
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import multiprocessing as mp

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover - tqdm is optional
    tqdm = None


EDGES_BY_NODE = None  # global for multiprocessing workers
MAX_EDGES_PER_NODE = None
MAX_TOTAL_EDGES = None


def normalize_entity(name: str) -> str:
    # 简单归一化：空格→下划线
    return name.replace(" ", "_")


def load_kg(kg_dir: Path):
    """Load KG edges and mappings."""
    edges_by_node = defaultdict(list)

    def load_split(fname: str):
        path = kg_dir / fname
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    continue
                h, r, t, ts = parts[0], parts[1], parts[2], parts[3]
                edge = (h, r, t, ts)
                edges_by_node[h].append(edge)
                edges_by_node[t].append(edge)  # 便于无向邻接检索

    # 读取 train/valid/test
    for split in ["train.txt", "valid.txt", "test.txt"]:
        load_split(split)

    return edges_by_node


def _init_pool(edges):
    # Initialize global KG cache for worker processes
    global EDGES_BY_NODE
    EDGES_BY_NODE = edges


def _dump_example(ex):
    return json.dumps(build_example(ex), ensure_ascii=False)


def build_example(example: Dict, edges_by_node=None, edge_label: str = "answer") -> Dict:
    """
    Build a Graph2Seq-style example from a MultiTQ QA item.
    优先使用 KG 中与答案实体相关的真实边；若无法对齐，则退化为星型图。
    """
    question = example["question"]
    answers: List[str] = example.get("answers", [])

    if edges_by_node is None:
        edges_by_node = EDGES_BY_NODE

    # 尝试用答案文本匹配实体名
    matched_nodes = []
    node_name_to_id = {}
    for idx, ans in enumerate(answers):
        cand = [ans, normalize_entity(ans)]
        found = None
        for c in cand:
            if c in edges_by_node:
                found = c
                break
        if found:
            node_name_to_id[found] = f"ans_{idx}"
            matched_nodes.append(found)

    # 如果能在 KG 找到至少一个相关节点，则构造真实子图
    if matched_nodes:
        nodes = set(matched_nodes)
        edges = []
        for n in matched_nodes:
            neigh = edges_by_node.get(n, [])
            if MAX_EDGES_PER_NODE:
                neigh = neigh[:MAX_EDGES_PER_NODE]
            edges.extend(neigh)

        if MAX_TOTAL_EDGES:
            edges = edges[:MAX_TOTAL_EDGES]

        # 边去重
        edges = list(dict.fromkeys(edges))

        g_node_names = {nid: nid for nid in nodes}
        g_edge_types = {}
        g_adj = defaultdict(dict)
        answer_ids = []

        for idx, n in enumerate(matched_nodes):
            answer_ids.append(n)

        for (h, r, t, ts) in edges:
            g_edge_types[r] = r
            if t in g_adj[h]:
                existing = g_adj[h][t]
                if isinstance(existing, list):
                    existing.append(r)
                else:
                    g_adj[h][t] = [existing, r]
            else:
                g_adj[h][t] = r

        # 确保答案节点在 g_node_names（上面已包含）
        out_graph = {
            "g_node_names": g_node_names,
            "g_edge_types": g_edge_types,
            "g_adj": dict(g_adj),
        }
    else:
        # 退化为星型图，保证可运行
        g_node_names = {"topic": "topic"}
        g_edge_types = {"e1": edge_label}
        g_adj = {"topic": {}}
        answer_ids = []
        for idx, ans in enumerate(answers):
            node_id = f"ans_{idx}"
            g_node_names[node_id] = ans
            g_adj["topic"][node_id] = "e1"
            answer_ids.append(node_id)
        out_graph = {
            "g_node_names": g_node_names,
            "g_edge_types": g_edge_types,
            "g_adj": g_adj,
        }

    out = {
        "inGraph": out_graph,
        "outSeq": question,
        "answers": answers,
        "topicEntityID": answer_ids[0] if answer_ids else "topic",
        "answer_ids": answer_ids,
        "meta": {
            "quid": example.get("quid"),
            "answer_type": example.get("answer_type"),
            "time_level": example.get("time_level"),
            "qtype": example.get("qtype"),
            "qlabel": example.get("qlabel"),
        },
    }
    return out


def convert_split(
    src_path: Path,
    dst_path: Path,
    edges_by_node,
    workers: int = 0,
    max_samples: int = 0,
) -> None:
    with src_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if max_samples and len(data) > max_samples:
        data = data[:max_samples]

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    if workers and workers > 1:
        with mp.Pool(processes=workers, initializer=_init_pool, initargs=(edges_by_node,)) as pool:
            iterator = pool.imap(_dump_example, data, chunksize=200)
            if tqdm is not None:
                iterator = tqdm(iterator, total=len(data), desc=f"convert {src_path.name}", unit="ex")
            with dst_path.open("w", encoding="utf-8") as fout:
                for line in iterator:
                    fout.write(line + "\n")
    else:
        iterator = data
        if tqdm is not None:
            iterator = tqdm(data, desc=f"convert {src_path.name}", unit="ex")
        with dst_path.open("w", encoding="utf-8") as fout:
            for ex in iterator:
                fout.write(json.dumps(build_example(ex, edges_by_node), ensure_ascii=False) + "\n")
    print(f"wrote {dst_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert MultiTQ QA JSON to minimal Graph2Seq format (star graph)."
    )
    parser.add_argument(
        "--questions_dir",
        type=Path,
        default=Path("dataset/MultiTQ/data/MultiTQ/questions"),
        help="Path to MultiTQ questions directory containing train/dev/test json.",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=Path,
        default=Path("Graph2Seq4TKGQG/data/MULTITQ"),
        help="Output directory for converted JSONL files (relative to repo root).",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=0,
        help="Number of worker processes for conversion (0/1 = single process).",
    )
    parser.add_argument(
        "--max_edges_per_node",
        type=int,
        default=0,
        help="Limit edges sampled per matched answer node (0=unlimited).",
    )
    parser.add_argument(
        "--max_total_edges",
        type=int,
        default=0,
        help="Limit total edges kept per example after sampling (0=unlimited).",
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=0,
        help="Limit number of samples per split (0=use all). Useful to downsample very large datasets.",
    )
    args = parser.parse_args()

    global MAX_EDGES_PER_NODE, MAX_TOTAL_EDGES
    MAX_EDGES_PER_NODE = args.max_edges_per_node if args.max_edges_per_node > 0 else None
    MAX_TOTAL_EDGES = args.max_total_edges if args.max_total_edges > 0 else None

    kg_dir = Path("dataset/MultiTQ/data/MultiTQ/kg")
    edges_by_node = load_kg(kg_dir)

    mapping = {
        "train.json": "train.json",
        "dev.json": "dev.json",
        "test.json": "test.json",
    }

    for src_name, dst_name in mapping.items():
        src = args.questions_dir / src_name
        dst = args.output_dir / dst_name
        if not src.exists():
            print(f"skip {src} (not found)")
            continue
        convert_split(
            src,
            dst,
            edges_by_node,
            workers=args.workers,
            max_samples=args.max_samples,
        )


if __name__ == "__main__":
    main()

