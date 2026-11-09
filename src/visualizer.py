"""PlantUML diagram generation and rendering module."""

import os
import urllib.error
import urllib.request
import zlib
from src.constants import (
    HTTP_STATUS_OK,
    REQUEST_TIMEOUT_SEC,
    ZERO,
)
from src.graph import DependencyGraph

PLANTUML_CHARS = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
)
PLANTUML_BASE_URL = "http://www.plantuml.com/plantuml"


def generate_plantuml_text(
    graph: DependencyGraph,
    root_node: str = "",
) -> str:
    """Generate PlantUML diagram source code from dependency graph."""
    lines = ["@startuml", "skinparam monochrome true"]

    for node in sorted(graph.nodes):
        if node == root_node:
            lines.append(f'rectangle "{node}" as {node} #LightBlue')
        else:
            lines.append(f'rectangle "{node}" as {node}')

    for src_pkg, tgt_pkg in sorted(graph.edges):
        lines.append(f"{src_pkg} --> {tgt_pkg}")

    lines.append("@enduml")
    return "\n".join(lines)


def _encode_plantuml_3bytes(byte1: int, byte2: int, byte3: int) -> str:
    """Convert 3 bytes into 4 characters using PlantUML 6-bit alphabet."""
    c1 = byte1 >> 2
    c2 = ((byte1 & 0x03) << 4) | (byte2 >> 4)
    c3 = ((byte2 & 0x0F) << 2) | (byte3 >> 6)
    c4 = byte3 & 0x3F
    return (
        PLANTUML_CHARS[c1 & 0x3F]
        + PLANTUML_CHARS[c2 & 0x3F]
        + PLANTUML_CHARS[c3 & 0x3F]
        + PLANTUML_CHARS[c4 & 0x3F]
    )


def encode_plantuml(text: str) -> str:
    """Compress and encode PlantUML text for server request."""
    raw_compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    result = []
    length = len(raw_compressed)
    idx = ZERO

    while idx < length:
        b1 = raw_compressed[idx]
        b2 = raw_compressed[idx + 1] if idx + 1 < length else ZERO
        b3 = raw_compressed[idx + 2] if idx + 2 < length else ZERO
        result.append(_encode_plantuml_3bytes(b1, b2, b3))
        idx += 3

    return "".join(result)


def _render_svg_nodes(nodes: list[str], root_node: str) -> tuple[list, dict]:
    """Render SVG rect and text elements for nodes."""
    box_w = 120
    box_h = 40
    gap_y = 60
    elements = []
    coords = {}

    for idx, node in enumerate(nodes):
        pos_x = 50 if node != root_node else 20
        pos_y = 30 + idx * gap_y
        coords[node] = (pos_x + box_w // 2, pos_y + box_h // 2)
        fill = "#bbf" if node == root_node else "#eef"
        elements.append(
            f'<rect x="{pos_x}" y="{pos_y}" width="{box_w}" height="{box_h}" '
            f'fill="{fill}" stroke="#333" rx="5"/>'
        )
        elements.append(
            f'<text x="{pos_x + 10}" y="{pos_y + 25}" '
            f'fill="#000">{node}</text>'
        )
    return elements, coords


def generate_standalone_svg(
    graph: DependencyGraph,
    root_node: str = "",
) -> str:
    """Generate offline SVG representation of dependency graph."""
    nodes = sorted(graph.nodes)
    gap_y = 60
    svg_height = max(200, len(nodes) * gap_y + 100)
    svg_width = 400

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_width}" height="{svg_height}">',
        '<style>text{font-family:sans-serif;font-size:14px;}</style>',
    ]

    node_elems, coords = _render_svg_nodes(nodes, root_node)
    elements.extend(node_elems)

    for src_pkg, tgt_pkg in graph.edges:
        if src_pkg in coords and tgt_pkg in coords:
            x1, y1 = coords[src_pkg]
            x2, y2 = coords[tgt_pkg]
            elements.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="#555" stroke-width="2"/>'
            )

    elements.append("</svg>")
    return "\n".join(elements)


def _try_fetch_plantuml_server(puml_text: str, svg_path: str) -> bool:
    """Try to render diagram via public PlantUML web service."""
    try:
        encoded = encode_plantuml(puml_text)
        url = f"{PLANTUML_BASE_URL}/svg/~1{encoded}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PlantUMLClient/1.0"},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
            if resp.status == HTTP_STATUS_OK:
                with open(svg_path, "wb") as img_handle:
                    img_handle.write(resp.read())
                return True
    except (urllib.error.URLError, OSError):
        return False
    return False


def save_and_render_diagram(
    graph: DependencyGraph,
    root_node: str,
    output_dir: str = "output",
) -> tuple[str, str]:
    """Save PlantUML and image file, returning saved file paths."""
    os.makedirs(output_dir, exist_ok=True)
    puml_text = generate_plantuml_text(graph, root_node)
    puml_path = os.path.join(output_dir, f"{root_node}_graph.puml")
    svg_path = os.path.join(output_dir, f"{root_node}_graph.svg")

    with open(puml_path, "w", encoding="utf-8") as handle:
        handle.write(puml_text)

    is_saved = _try_fetch_plantuml_server(puml_text, svg_path)
    if not is_saved:
        offline_svg = generate_standalone_svg(graph, root_node)
        with open(svg_path, "w", encoding="utf-8") as img_handle:
            img_handle.write(offline_svg)

    return puml_path, svg_path


def get_visualizer_comparison_notes() -> list[str]:
    """Return comparison notes between our tool and pipdeptree."""
    return [
        "1. Источник данных:",
        "   - Наш инструмент анализирует метаданные репозитория (PyPI/тест)",
        "     без необходимости предварительной установки пакетов в систему.",
        "   - pipdeptree анализирует только локально установленные пакеты в",
        "     текущем virtualenv (через importlib.metadata).",
        "2. Формат визуализации:",
        "   - Наш инструмент формирует чистую диаграмму PlantUML (@startuml)",
        "     и напрямую рендерит изображение графа (SVG/PNG).",
        "   - pipdeptree выводит дерево в терминал или требует Graphviz dot.",
        "3. Фильтрация и глубина:",
        "   - Наш инструмент поддерживает фильтрацию по подстроке и глубине,",
        "     а также явно выявляет и изолирует циклические ребра.",
    ]
