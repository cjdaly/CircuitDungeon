# SPDX-License-Identifier: MIT
# main.py and hardware.py only run on the board, so nothing else here imports
# them. This reads both as source and checks every hardware.<name> main.py uses
# is defined, the kind of slip that otherwise only shows up as a black screen
# (2026-11-07: an edit dropped init_touch).
#
#   python3 Chapter_9/tests/test_main_wiring.py

import ast
import os
import unittest

_GAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")


def _tree(name):
    with open(os.path.join(_GAME, name)) as f:
        return ast.parse(f.read())


class TestMainWiring(unittest.TestCase):
    def test_every_hardware_name_main_uses_exists(self):
        defined = set()
        for node in _tree("hardware.py").body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Assign):
                defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
        used = {
            node.attr
            for node in ast.walk(_tree("main.py"))
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "hardware"
        }
        self.assertTrue(used)
        self.assertEqual(used - defined, set())


if __name__ == "__main__":
    unittest.main()
