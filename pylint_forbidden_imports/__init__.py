from typing import Optional, List, Union, Set

from astroid import Import, Module, ImportFrom, AstroidBuildingException
from astroid.context import InferenceContext
from astroid.node_classes import NodeNG
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker


class ForbiddenImportChecker(BaseChecker):
    """Pylint checker that enforces forbidden import"""

    __implements__ = IAstroidChecker

    name = "forbidden-import"
    priority = -1
    msgs = {
        "E6901": (
            "Not allowed to import %s here, %s is a forbidden module",
            "forbidden-import",
            "Refactor your code to remove this import.",
        ),
        "E6902": (
            "Importing %s causes %s, a forbidden module, to be imported",
            "forbidden-transitive-import",
            "Refactor your code to remove this import.",
        ),
    }
    options = (
        (
            "forbidden-imports",
            {
                "default": (),
                "type": "csv",
                "metavar": "<module:forbidden;imports>",
                "help": (
                    "Colon/semicolon-delimited sets of names that determine"
                    " what modules are allowed to be imported"
                    " from another module"
                ),
            },
        ),
        (
            "forbidden-import-recurse",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y_or_n>",
                "help": "Check forbidden imports recursively",
            },
        ),
    )

    def __init__(self, linter=None):
        super().__init__(linter)
        self._forbidden_imports = {}
        self._recursive = False

    def open(self):
        for group in self.config.forbidden_imports:
            root_module, forbidden_import_str = group.split(":")
            self._forbidden_imports[root_module] = forbidden_import_str.split(";")
        self._recursive = self.config.forbidden_import_recurse

    @staticmethod
    def _infer_name_module(node, name):
        context = InferenceContext()
        context.lookupname = name
        return node.infer(context, asname=False)

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

    def _get_forbidden_imports_for_node(self, node: NodeNG) -> List[str]:
        """Get list of forbidden imports for a given node"""
        module = self._get_parent_module(node)
        if module is None:
            return []

        # Get list of forbidden imports for this module
        forbidden_imports = set()
        for module_prefix in self._forbidden_imports:
            if module.name.startswith(module_prefix):
                forbidden_imports.update(self._forbidden_imports[module_prefix])
        return list(forbidden_imports)

    @staticmethod
    def _import_module(node: Union[Import, ImportFrom], name: str) -> Optional[Module]:
        if isinstance(node, Import):
            try:
                return node.do_import_module(name)
            except AstroidBuildingException:
                return None

        try:
            return node.do_import_module(f"{node.modname}.{name}")
        except AstroidBuildingException:
            pass

        try:
            return node.do_import_module(node.modname)
        except AstroidBuildingException:
            pass

        return None

    def _check_forbidden_imports(self, node: Union[Import, ImportFrom]):
        forbidden_imports = self._get_forbidden_imports_for_node(node)
        if not forbidden_imports:
            return

        for name, _ in node.names:
            import_name = name
            if isinstance(node, ImportFrom):
                import_name = f"{node.modname}.{name}"

            has_forbidden_imports = False
            for forbidden_import in forbidden_imports:
                if import_name.startswith(forbidden_import):
                    self.add_message(
                        "forbidden-import",
                        node=node,
                        args=(import_name, forbidden_import),
                    )
                    has_forbidden_imports = True

            if not self._recursive:
                return

            # If we have any forbidden imports, no point checking the transitive ones
            if has_forbidden_imports:
                return

            module = self._import_module(node, name)
            if not module:
                continue
            transitive_imports = self._get_forbidden_transitive_imports(
                module, forbidden_imports
            )
            for transitive_import in transitive_imports:
                self.add_message(
                    "forbidden-transitive-import",
                    node=node,
                    args=(import_name, transitive_import),
                )

    def _get_forbidden_transitive_imports(
        self, root_module: Module, forbidden_imports: List[str]
    ) -> Set[str]:
        bad_imports: Set[str] = set()
        checked_modules: Set[str] = set()
        modules_to_check: Set[Module] = {root_module}

        while modules_to_check:
            module = modules_to_check.pop()
            if module.name in checked_modules:
                continue
            checked_modules.add(module.name)

            # Check imports in the module
            for forbidden_import in forbidden_imports:
                if module.name.startswith(forbidden_import):
                    bad_imports.add(module.name)
                    continue

            # Gather all the imported modules and queue them for checking
            for node in module.get_children():
                if not isinstance(node, (Import, ImportFrom)):
                    continue
                for name, _ in node.names:
                    imported_module = self._import_module(node, name)
                    if imported_module:
                        modules_to_check.add(imported_module)

        return bad_imports

    def visit_import(self, node):
        """check import isn't forbidden"""
        if not isinstance(node, Import):
            return
        self._check_forbidden_imports(node)

    def visit_importfrom(self, node):
        """check import isn't forbidden"""
        if not isinstance(node, ImportFrom):
            return
        self._check_forbidden_imports(node)


def register(linter):
    """Required to register the plugin with pylint"""
    linter.register_checker(ForbiddenImportChecker(linter))
