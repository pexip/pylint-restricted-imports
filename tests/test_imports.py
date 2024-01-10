from pathlib import Path
from unittest import mock

import astroid
from astroid import nodes

from pylint.testutils import CheckerTestCase, MessageTest

from pylint_restricted_imports import RestrictedImportChecker

INPUT_DIR = Path(__file__).absolute().parent / "input"


class TestRestrictedImportChecker(CheckerTestCase):
    """restricted Import Checker Tests"""

    CHECKER_CLASS = RestrictedImportChecker
    CONFIG = {
        "restricted_imports": ["foo:bar"],
        "restricted_import_recurse": False,
    }

    def test_no_restricted_import(self):
        """test no restricted imports from import"""
        node = astroid.extract_node("import baz", "foo")
        with mock.patch.object(self.checker, "_import_module") as mock_import:
            mod = nodes.Module("baz")
            mod.doc_node = "baz"
            mock_import.return_value = mod
            with self.assertNoMessages():
                self.checker.visit_import(node)

    def test_no_restricted_importfrom(self):
        """test no restricted imports from import from"""
        node = astroid.extract_node("from baz import wibble", "foo")
        with mock.patch.object(self.checker, "_import_module") as mock_import:
            mod = nodes.Module("baz.wibble")
            mod.doc_node = "baz.wibble"
            mock_import.return_value = mod
            with self.assertNoMessages():
                self.checker.visit_importfrom(node)

    def test_restricted_import(self):
        """test restricted import"""
        node = astroid.extract_node("import bar", "foo")
        with mock.patch.object(self.checker, "_import_module") as mock_import:
            mod = nodes.Module("bar")
            mod.doc_node = "bar"
            mock_import.return_value = mod
            with self.assertAddsMessages(
                MessageTest(
                    "restricted-import",
                    line=1,
                    end_line=1,
                    col_offset=0,
                    end_col_offset=10,
                    node=node,
                    args=("bar", "bar"),
                )
            ):
                self.checker.visit_import(node)

    def test_restricted_importfrom(self):
        """test restricted import from"""
        node = astroid.extract_node("from bar import wibble", "foo")

        with mock.patch.object(self.checker, "_import_module") as mock_import:
            mod = nodes.Module("bar.wibble")
            mod.doc_node = "bar.wibble"
            mock_import.return_value = mod
            with self.assertAddsMessages(
                MessageTest(
                    "restricted-import",
                    line=1,
                    end_line=1,
                    col_offset=0,
                    end_col_offset=22,
                    node=node,
                    args=("bar.wibble", "bar"),
                )
            ):
                self.checker.visit_importfrom(node)

    def test_recursive_import(self):
        """test recursive import"""
        self.CONFIG["restricted_import_recurse"] = True
        self.setup_method()

        node = astroid.extract_node("import baz", "foo")
        baz_module = astroid.extract_node("import bar", "baz").parent
        with mock.patch.object(self.checker, "_import_module") as mock_import_module:
            mod = nodes.Module("bar")
            mod.doc_node = "bar module"
            mock_import_module.side_effect = [
                baz_module,
                baz_module,
                mod,
            ]
            with self.assertAddsMessages(
                MessageTest(
                    "restricted-transitive-import",
                    line=1,
                    end_line=1,
                    col_offset=0,
                    end_col_offset=10,
                    node=node,
                    args=("baz", "bar"),
                )
            ):
                self.checker.visit_import(node)

    def test_recursive_importfrom(self):
        """test recursive importfrom"""
        self.CONFIG["restricted_import_recurse"] = True
        self.setup_method()

        node = astroid.extract_node("from baz import wibble", "foo")
        baz_wibble_module = astroid.extract_node(
            "from bar import Wibble", "baz.wibble"
        ).parent
        with mock.patch.object(self.checker, "_import_module") as mock_import_module:
            mod = nodes.Module("bar")
            mod.doc_node = "bar module"
            mock_import_module.side_effect = [
                baz_wibble_module,
                baz_wibble_module,
                mod,
            ]
            with self.assertAddsMessages(
                MessageTest(
                    "restricted-transitive-import",
                    line=1,
                    end_line=1,
                    col_offset=0,
                    end_col_offset=22,
                    node=node,
                    args=("baz.wibble", "bar"),
                )
            ):
                self.checker.visit_importfrom(node)
