from pathlib import Path
from unittest import mock

import astroid

from pylint.testutils import CheckerTestCase, Message

from pylint_forbidden_imports import ForbiddenImportChecker

INPUT_DIR = Path(__file__).absolute().parent / "input"


class TestForbiddenImportChecker(CheckerTestCase):
    """Forbidden Import Checker Tests"""

    CHECKER_CLASS = ForbiddenImportChecker
    CONFIG = {
        "forbidden_imports": ["foo:bar"],
        "forbidden_import_recurse": "n",
    }

    def test_no_forbidden_import(self):
        """test no forbidden imports from import"""
        node = astroid.extract_node("import baz", "foo")
        with self.assertNoMessages():
            self.checker.visit_import(node)

    def test_no_forbidden_importfrom(self):
        """test no forbidden imports from import from"""
        node = astroid.extract_node("from baz import wibble", "foo")
        with self.assertNoMessages():
            self.checker.visit_importfrom(node)

    def test_forbidden_import(self):
        """test forbidden import"""
        node = astroid.extract_node("import bar", "foo")
        with self.assertAddsMessages(
            Message("forbidden-import", node=node, args=("bar", "bar"))
        ):
            self.checker.visit_import(node)

    def test_forbidden_importfrom(self):
        """test forbidden import from"""
        node = astroid.extract_node("from bar import wibble", "foo")
        with self.assertAddsMessages(
              Message("forbidden-import", node=node, args=("bar.wibble", "bar"))
        ):
            self.checker.visit_importfrom(node)

    def test_recursive_import(self):
        """test recursive import"""
        self.CONFIG["forbidden_import_recurse"] = "y"
        node = astroid.extract_node("import baz", "foo")
        with mock.patch.object(self.checker, "_import_module") as mock_import_module:
            mock_import_module.side_effect = [
                astroid.extract_node("import bar", "baz").parent,
                astroid.Module("bar", "bar module"),
            ]
            with self.assertAddsMessages(
                Message("forbidden-transitive-import", node=node, args=("baz", "bar"))
            ):
                self.checker.visit_import(node)

    def test_recursive_importfrom(self):
        """test recursive importfrom"""
        self.CONFIG["forbidden_import_recurse"] = "y"
        node = astroid.extract_node("from baz import wibble", "foo")
        with mock.patch.object(self.checker, "_import_module") as mock_import_module:
            mock_import_module.side_effect = [
                astroid.extract_node("from bar import wibble", "baz").parent,
                astroid.Module("bar", "bar module"),
            ]
            with self.assertAddsMessages(
                Message("forbidden-transitive-import", node=node, args=("baz.wibble", "bar"))
            ):
                self.checker.visit_importfrom(node)
