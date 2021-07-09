from collections import defaultdict
from typing import Optional, List, Union, Set, Dict

from astroid import Import, Module, ImportFrom, AstroidBuildingException
from astroid.node_classes import NodeNG
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker


class RestrictedImportChecker(BaseChecker):
    """Pylint checker that enforces restricted import"""

    __implements__ = IAstroidChecker

    name = "restricted-import"
    priority = -1
    msgs = {
        "E6901": (
            "Not allowed to import %s here, %s is a restricted module",
            "restricted-import",
            "Refactor your code to remove this import.",
        ),
        "E6902": (
            "Importing %s causes %s, a restricted module, to be imported",
            "restricted-transitive-import",
            "Refactor your code to remove this import.",
        ),
    }
    options = (
        (
            "restricted-imports",
            {
                "default": (),
                "type": "csv",
                "metavar": "<module:restricted;imports>",
                "help": (
                    "Colon/semicolon-delimited sets of names that determine"
                    " what modules are allowed to be imported"
                    " from another module"
                ),
            },
        ),
        (
            "restricted-import-recurse",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "Check restricted imports recursively",
            },
        ),
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        self._restricted_imports = {}
        self._recursive = False
        self._imports: Dict[str, Set[str]] = defaultdict(set)

    def open(self):
        for group in self.config.restricted_imports:
            root_module, restricted_import_str = group.split(":")
            self._restricted_imports[root_module] = restricted_import_str.split(";")
        self._recursive = self.config.restricted_import_recurse

    @staticmethod
    def _get_parent_module(node: NodeNG) -> Optional[Module]:
        """Get the parent module for a node"""
        while not isinstance(node, Module):
            if node.parent is None:
                # Failed to find parent module
                return None
            node = node.parent
        assert isinstance(node, Module)
        return node

    def _get_restricted_imports_for_module(self, module: Optional[Module]) -> List[str]:
        """Get list of restricted imports for a given node"""
        if module is None:
            return []

        # Get list of restricted imports for this module
        restricted_imports = set()
        for module_prefix in self._restricted_imports:
            if module.name.startswith(module_prefix):
                restricted_imports.update(self._restricted_imports[module_prefix])
        return list(restricted_imports)

    @staticmethod
    def _import_module(node: Union[Import, ImportFrom], name: str) -> Optional[Module]:
        module = None
        if isinstance(node, Import):
            try:
                module = node.do_import_module(name)
            except AstroidBuildingException:
                return None
        elif node.modname:
            try:
                module = node.do_import_module(f"{node.modname}.{name}")
            except AstroidBuildingException:
                pass

            if not module:
                try:
                    module = node.do_import_module(node.modname)
                except AstroidBuildingException:
                    pass

        if isinstance(module, Module):
            return module
        return None

    def _gather_imports(self, module: Module):
        for node in module.get_children():
            if not isinstance(node, (Import, ImportFrom)):
                continue
            for name, _ in node.names:
                imported_module = self._import_module(node, name)
                if not imported_module:
                    continue
                self._imports[module.name].add(imported_module.name)
                if imported_module.name in self._imports:
                    continue
                if self._recursive and imported_module:
                    self._gather_imports(imported_module)

    def _check_restricted_imports(self, node: Union[Import, ImportFrom]):
        parent_module = self._get_parent_module(node)
        if not parent_module:
            return

        restricted_imports = self._get_restricted_imports_for_module(parent_module)
        if not restricted_imports:
            return

        modules = [self._import_module(node, n) for n, _ in node.names]
        modules = [m for m in modules if m is not None]

        has_restricted_imports = False
        for module in modules:
            for restricted_import in restricted_imports:
                if module.name.startswith(restricted_import):
                    has_restricted_imports = True
                    self.add_message(
                        "restricted-import",
                        node=node,
                        args=(module.name, restricted_import),
                    )

        if not self._recursive:
            return

        # If we have any restricted imports, no point checking the transitive ones
        if has_restricted_imports:
            return

        if parent_module.name not in self._imports:
            self._gather_imports(parent_module)

        for module in modules:
            transitive_import = self._get_restricted_transitive_imports(
                module.name, restricted_imports
            )
            if transitive_import:
                self.add_message(
                    "restricted-transitive-import",
                    node=node,
                    args=(module.name, transitive_import),
                )
                return

    def _get_restricted_transitive_imports(
        self, import_name: str, restricted_imports: List[str]
    ) -> Optional[str]:
        checked_modules: Set[str] = set()
        modules_to_check: Set[str] = {import_name}

        while modules_to_check:
            module_name = modules_to_check.pop()
            if module_name in checked_modules:
                continue
            checked_modules.add(module_name)

            # Gather all the imported modules and queue them for checking
            for import_name in self._imports[module_name]:
                for restricted_import in restricted_imports:
                    if import_name.startswith(restricted_import):
                        return import_name
            modules_to_check.update(self._imports[module_name])

        return None

    def visit_import(self, node):
        """check import isn't restricted"""
        if not isinstance(node, Import):
            return
        self._check_restricted_imports(node)

    def visit_importfrom(self, node):
        """check import isn't restricted"""
        if not isinstance(node, ImportFrom):
            return
        self._check_restricted_imports(node)


def register(linter):
    """Required to register the plugin with pylint"""
    linter.register_checker(RestrictedImportChecker(linter))
