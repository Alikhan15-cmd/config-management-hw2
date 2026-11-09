"""Unit tests for PlantUML visualizer and rendering."""

import os
import shutil
import tempfile
import unittest
from src.constants import ZERO
from src.graph import DependencyGraph
from src.visualizer import (
    encode_plantuml,
    generate_plantuml_text,
    generate_standalone_svg,
    get_visualizer_comparison_notes,
    save_and_render_diagram,
)


class TestVisualizer(unittest.TestCase):
    """Test suite for diagram generation and rendering."""

    def setUp(self):
        """Prepare graph fixture."""
        self.graph = DependencyGraph()
        self.graph.add_edge("A", "B")
        self.graph.add_edge("A", "C")
        self.graph.add_edge("B", "D")

    def test_generate_plantuml_text(self):
        """Verify PlantUML syntax structure."""
        puml = generate_plantuml_text(self.graph, "A")
        self.assertIn("@startuml", puml)
        self.assertIn("@enduml", puml)
        self.assertIn("A --> B", puml)
        self.assertIn("A --> C", puml)
        self.assertIn("B --> D", puml)

    def test_encode_plantuml(self):
        """Verify PlantUML deflate encoding."""
        encoded = encode_plantuml("Bob -> Alice : hello")
        self.assertGreater(len(encoded), ZERO)
        self.assertIsInstance(encoded, str)

    def test_generate_standalone_svg(self):
        """Verify standalone SVG output."""
        svg = generate_standalone_svg(self.graph, "A")
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertIn("<rect", svg)
        self.assertIn("<line", svg)

    def test_save_and_render_diagram(self):
        """Verify saving puml and svg files."""
        temp_dir = tempfile.mkdtemp()
        try:
            puml_path, svg_path = save_and_render_diagram(
                self.graph, "A", output_dir=temp_dir
            )
            self.assertTrue(os.path.isfile(puml_path))
            self.assertTrue(os.path.isfile(svg_path))
            self.assertGreater(os.path.getsize(puml_path), ZERO)
            self.assertGreater(os.path.getsize(svg_path), ZERO)
        finally:
            shutil.rmtree(temp_dir)

    def test_comparison_notes(self):
        """Verify visualizer comparison notes are present."""
        notes = get_visualizer_comparison_notes()
        self.assertGreater(len(notes), ZERO)


if __name__ == "__main__":
    unittest.main()
