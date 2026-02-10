import time
import os
import numpy as np
from collections import defaultdict

def load_graph():
    graph = {}
    incoming = defaultdict(list)

    print("Loading files from local disk...")

    files = os.listdir("pages")
    print(f"Found {len(files)} files.")

    for fname in files:
        page = fname.replace(".txt", "")
        with open(os.path.join("pages", fname)) as f:
            links = [line.strip() for line in f if line.strip()]

        graph[page] = links
        for dst in links:
            incoming[dst].append(page)

    print("Finished loading all files.")
    return graph, incoming

def pagerank(graph, incoming, damping=0.85, tol=0.005, max_iters=100):
    n = len(graph)
    pr = {p: 1.0 / n for p in graph}

    for it in range(max_iters):
        new_pr = {}
        dangling_sum = sum(pr[p] for p in graph if len(graph[p]) == 0)

        for page in graph:
            rank_sum = 0.0
            for src in incoming.get(page, []):
                rank_sum += pr[src] / len(graph[src])

            new_pr[page] = (1 - damping) / n + damping * (rank_sum + dangling_sum / n)

        diff = abs(sum(new_pr.values()) - sum(pr.values())) / sum(pr.values())
        print(f"Iteration {it + 1}, diff={diff:.6f}")

        pr = new_pr
        if diff <= tol:
            break

    return pr

def stats(arr):
    return {
        "avg": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "min": int(np.min(arr)),
        "max": int(np.max(arr)),
        "quintiles": np.percentile(arr, [20, 40, 60, 80]).tolist()
    }

def main():
    start = time.time()

    graph, incoming = load_graph()

    outgoing = np.array([len(v) for v in graph.values()])
    incoming_counts = np.array([len(incoming[p]) for p in graph])

    print("Outgoing stats:", stats(outgoing))
    print("Incoming stats:", stats(incoming_counts))

    print("\nRunning PageRank...")
    pr_start = time.time()
    pr = pagerank(graph, incoming)
    pr_time = time.time() - pr_start

    print("\nTop 5 pages by PageRank:")
    for page, score in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(page, score)

    print("\nTiming (seconds)")
    print("PageRank:", pr_time)
    print("Total:", time.time() - start)

if __name__ == "__main__":
    main()
