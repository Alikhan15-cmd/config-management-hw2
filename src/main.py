"""CLI entry point for dependency graph visualizer."""

import argparse
import sys
from src.collector import CollectorError, get_direct_dependencies
from src.config import ConfigError, load_config
from src.constants import (
    DEFAULT_CONFIG_PATH,
    EXIT_CODE_ERROR,
    EXIT_CODE_SUCCESS,
    FIVE,
    FOUR,
    ONE,
    THREE,
    TWO,
    ZERO,
)
from src.graph import build_dependency_graph
from src.order import compute_load_order, get_pip_comparison_notes
from src.visualizer import (
    generate_plantuml_text,
    get_visualizer_comparison_notes,
    save_and_render_diagram,
)


def build_argument_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Dependency Graph Visualizer for Python packages (pip)"
    )
    parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG_PATH,
        help="Path to JSON configuration file (default: config.json)",
    )
    parser.add_argument(
        "--stage",
        "-s",
        type=int,
        default=FIVE,
        choices=[1, 2, 3, 4, 5],
        help="Target stage to execute (1..5, default: 5)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run Stage 5 demonstration on 3 distinct packages",
    )
    return parser


def run_stage_one(config_path: str) -> int:
    """Execute Stage 1: load config and display parameters."""
    config = load_config(config_path)
    print("=== Этап 1. Параметры конфигурации ===")
    print(config.format_key_value())
    return EXIT_CODE_SUCCESS


def run_stage_two(config_path: str) -> int:
    """Execute Stage 2: display direct dependencies."""
    config = load_config(config_path)
    deps = get_direct_dependencies(
        package_name=config.package_name,
        version=config.package_version,
        repo_url=config.repository_url,
        test_mode=config.test_mode,
    )
    header = (
        f"=== Этап 2. Прямые зависимости пакета "
        f"{config.package_name} ({config.package_version}) ==="
    )
    print(header)
    if len(deps) == ZERO:
        print("Прямые зависимости отсутствуют.")
    else:
        for dep in deps:
            print(f"- {dep}")
    return EXIT_CODE_SUCCESS


def run_stage_three(config_path: str) -> int:
    """Execute Stage 3: build graph using recursive DFS and display."""
    config = load_config(config_path)
    graph = build_dependency_graph(
        root_package=config.package_name,
        version=config.package_version,
        repo_url=config.repository_url,
        test_mode=config.test_mode,
        max_depth=config.max_depth,
        filter_substring=config.filter_substring,
    )
    print("=== Этап 3. Построение графа зависимостей (DFS) ===")
    print(f"Корень: {config.package_name} (глубина: {config.max_depth})")
    print(f"Вершины ({len(graph.nodes)}): {', '.join(sorted(graph.nodes))}")
    print(f"Ребра ({len(graph.edges)}):")
    for src_node, tgt_node in sorted(graph.edges):
        print(f"  {src_node} -> {tgt_node}")

    if len(graph.cycles) > ZERO:
        print(f"Обнаружены циклы ({len(graph.cycles)}):")
        for cycle in graph.cycles:
            print(f"  {' -> '.join(cycle)}")
    else:
        print("Циклических зависимостей не обнаружено.")

    return EXIT_CODE_SUCCESS


def run_stage_four(config_path: str) -> int:
    """Execute Stage 4: compute and display load order."""
    config = load_config(config_path)
    graph = build_dependency_graph(
        root_package=config.package_name,
        version=config.package_version,
        repo_url=config.repository_url,
        test_mode=config.test_mode,
        max_depth=config.max_depth,
        filter_substring=config.filter_substring,
    )
    order = compute_load_order(graph, config.package_name)
    print(f"=== Этап 4. Порядок загрузки пакета {config.package_name} ===")
    for idx, pkg in enumerate(order, start=ONE):
        print(f"  {idx}. {pkg}")

    print("\n=== Сравнение с менеджером пакетов (pip) ===")
    for note in get_pip_comparison_notes():
        print(note)

    return EXIT_CODE_SUCCESS


def _visualize_single_package(
    pkg: str,
    ver: str,
    repo_url: str,
    test_mode: bool,
    max_depth: int,
    filter_sub: str,
) -> None:
    """Build, render and display diagram for a package."""
    graph = build_dependency_graph(
        root_package=pkg,
        version=ver,
        repo_url=repo_url,
        test_mode=test_mode,
        max_depth=max_depth,
        filter_substring=filter_sub,
    )
    puml_text = generate_plantuml_text(graph, pkg)
    print(f"--- PlantUML диаграмма для {pkg} ---")
    print(puml_text)

    puml_path, svg_path = save_and_render_diagram(graph, pkg)
    print(f"PlantUML сохранен: {puml_path}")
    print(f"Изображение графа сохранено: {svg_path}\n")


def run_stage_five(config_path: str, run_demo: bool = False) -> int:
    """Execute Stage 5: PlantUML diagram generation and visualization."""
    config = load_config(config_path)
    print("=== Этап 5. Визуализация графа зависимостей (PlantUML) ===")

    _visualize_single_package(
        config.package_name,
        config.package_version,
        config.repository_url,
        config.test_mode,
        config.max_depth,
        config.filter_substring,
    )

    if run_demo:
        print("=== Демонстрация на 3 пакетах тестового репозитория ===")
        demos = [
            ("A", "test_repos/simple_repo.json"),
            ("A", "test_repos/cyclic_repo.json"),
            ("A", "test_repos/diamond_repo.json"),
        ]
        for name, repo_file in demos:
            _visualize_single_package(
                name, "1.0.0", repo_file, True, 5, ""
            )

    print("=== Сравнение со штатными средствами (pipdeptree) ===")
    for note in get_visualizer_comparison_notes():
        print(note)

    return EXIT_CODE_SUCCESS


def main(argv=None) -> int:
    """Main CLI entry point."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    try:
        if args.stage == ONE:
            return run_stage_one(args.config)
        if args.stage == TWO:
            return run_stage_two(args.config)
        if args.stage == THREE:
            return run_stage_three(args.config)
        if args.stage == FOUR:
            return run_stage_four(args.config)
        return run_stage_five(args.config, run_demo=args.demo)
    except (ConfigError, CollectorError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return EXIT_CODE_ERROR
    except Exception as err:
        print(f"Unexpected error: {err}", file=sys.stderr)
        return EXIT_CODE_ERROR


if __name__ == "__main__":
    sys.exit(main())
