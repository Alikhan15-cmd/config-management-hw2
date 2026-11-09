"""Dependency load order calculation and comparison logic."""

from src.constants import ZERO
from src.graph import DependencyGraph


def compute_load_order(graph: DependencyGraph, root_node: str) -> list[str]:
    """Compute bottom-up load/installation order via post-order DFS."""
    order = []
    visited = set()
    rec_stack = set()

    def _post_order_visit(node: str) -> None:
        """DFS post-order traversal helper."""
        if node in visited or node not in graph.adjacency:
            return

        rec_stack.add(node)
        for child in graph.adjacency.get(node, []):
            if child in rec_stack:
                continue
            if child not in visited:
                _post_order_visit(child)

        rec_stack.remove(node)
        visited.add(node)
        order.append(node)

    if root_node in graph.nodes:
        _post_order_visit(root_node)

    return order


def get_pip_comparison_notes() -> list[str]:
    """Return analytical comparison notes with pip package manager."""
    return [
        "1. Алгоритм разрешения: pip использует backtracking-резолвер "
        "(resolvelib)",
        "   для поиска совместимого набора версий при конфликтах.",
        "2. Учет окружения: pip проверяет маркеры платформы и версии Python",
        "   (sys_platform, python_version) и не устанавливает неподходящие.",
        "3. Локальный кэш и установленные пакеты: pip пропускает зависимости,",
        "   уже присутствующие в текущем virtualenv.",
        "4. Циклические зависимости: pip разрывает циклы в процессе сборки,",
        "   устанавливая пакеты без вызова setup.py на этапе рантайма.",
    ]
