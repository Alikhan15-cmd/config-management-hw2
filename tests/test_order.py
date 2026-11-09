"""Unit tests for dependency load order resolution."""

import os
import unittest
from src.constants import ZERO
from src.graph import build_dependency_graph
from src.order import compute_load_order, get_pip_comparison_notes


class TestOrder(unittest.TestCase):
    """Test suite for post-order dependency loading."""

    def test_simple_tree_load_order(self):
        """Verify prerequisites precede dependent packages."""
        repo_path = os.path.join("test_repos", "simple_repo.json")
        graph = build_dependency_graph(
            root_package="A",
            version="1.0.0",
            repo_url=repo_path,
            test_mode=True,
            max_depth=5,
            filter_substring="",
        )
        order = compute_load_order(graph, "A")
        self.assertEqual(order[-1], "A")
        self.assertLess(order.index("D"), order.index("B"))
        self.assertLess(order.index("E"), order.index("C"))
        self.assertLess(order.index("B"), order.index("A"))
        self.assertLess(order.index("C"), order.index("A"))

    def test_diamond_load_order(self):
        """Verify diamond dependencies appear once and before dependents."""
        repo_path = os.path.join("test_repos", "diamond_repo.json")
        graph = build_dependency_graph(
            root_package="A",
            version="1.0.0",
            repo_url=repo_path,
            test_mode=True,
            max_depth=5,
            filter_substring="",
        )
        order = compute_load_order(graph, "A")
        self.assertEqual(len(order), 4)
        self.assertEqual(order[-1], "A")
        self.assertLess(order.index("D"), order.index("B"))
        self.assertLess(order.index("D"), order.index("C"))

    def test_cyclic_load_order(self):
        """Verify cycle handling does not produce duplicate nodes."""
        repo_path = os.path.join("test_repos", "cyclic_repo.json")
        graph = build_dependency_graph(
            root_package="A",
            version="1.0.0",
            repo_url=repo_path,
            test_mode=True,
            max_depth=5,
            filter_substring="",
        )
        order = compute_load_order(graph, "A")
        self.assertEqual(len(order), len(set(order)))
        self.assertIn("A", order)
        self.assertIn("B", order)

    def test_pip_comparison_notes(self):
        """Verify comparison notes are present."""
        notes = get_pip_comparison_notes()
        self.assertGreater(len(notes), ZERO)


if __name__ == "__main__":
    unittest.main()
