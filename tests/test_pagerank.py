import unittest
from src.analyze_pagerank import pagerank

class TestPageRank(unittest.TestCase):

    def test_simple_cycle_graph(self):
        """
        A -> B -> C -> A
        All nodes should have equal PageRank.
        """
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

        pr = pagerank(graph, incoming, max_iters=100)

        self.assertAlmostEqual(pr["A"], pr["B"], places=4)
        self.assertAlmostEqual(pr["B"], pr["C"], places=4)

    def test_rank_sum_to_one(self):
        """
        PageRank values should sum to 1.
        """
        graph = {
            "A": ["B", "C"],
            "B": ["C"],
            "C": []
        }

        incoming = {
            "B": ["A"],
            "C": ["A", "B"],
            "A": []
        }

        pr = pagerank(graph, incoming, max_iters=100)

        self.assertAlmostEqual(sum(pr.values()), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
