from src.analyze_pagerank import pagerank

def test_simple_cycle():
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    incoming = {
        "A": ["C"],
        "B": ["A"],
        "C": ["B"]
    }

    pr = pagerank(graph, incoming, tol=0.0001)

    values = list(pr.values())
    assert max(values) - min(values) < 0.01
