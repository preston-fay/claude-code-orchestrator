"""Dead code detection using static analysis."""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict

from .config import HygieneConfig


class DeadCodeAnalyzer(ast.NodeVisitor):
    """AST visitor for dead code detection."""

    def __init__(self, source_code: str, filepath: Path):
        self.source = source_code
        self.filepath = filepath
        self.lines = source_code.split("\n")

        # Track definitions
        self.defined_functions: Set[str] = set()
        self.defined_classes: Set[str] = set()
        self.defined_vars: Set[str] = set()
        self.imports: Set[str] = set()

        # Track usage
        self.used_names: Set[str] = set()

        # Results
        self.unused_functions: List[Dict] = []
        self.unused_classes: List[Dict] = []
        self.unused_imports: List[Dict] = []

    def visit_FunctionDef(self, node):
        """Visit function definition."""
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definition."""
        self.defined_classes.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Visit from...import statement."""
        for alias in node.names:
            if alias.name != "*":
                name = alias.asname if alias.asname else alias.name
                self.imports.add(name)
        self.generic_visit(node)

    def visit_Name(self, node):
        """Visit name reference."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit attribute access."""
        # Track attribute usage
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Visit function call."""
        if isinstance(node.func, ast.Name):
            self.used_names.add(node.func.id)
        self.generic_visit(node)

    def analyze(self) -> None:
        """Run analysis to find unused code."""
        try:
            tree = ast.parse(self.source, filename=str(self.filepath))
            self.visit(tree)

            # Find unused functions
            for func_name in self.defined_functions:
                if func_name not in self.used_names and not func_name.startswith("_"):
                    # Find line number
                    lineno = self._find_definition_line(func_name, "def")
                    if lineno:
                        self.unused_functions.append(
                            {
                                "name": func_name,
                                "file": str(self.filepath),
                                "line": lineno,
                                "type": "function",
                            }
                        )

            # Find unused classes
            for class_name in self.defined_classes:
                if class_name not in self.used_names:
                    lineno = self._find_definition_line(class_name, "class")
                    if lineno:
                        self.unused_classes.append(
                            {
                                "name": class_name,
                                "file": str(self.filepath),
                                "line": lineno,
                                "type": "class",
                            }
                        )

            # Find unused imports
            for import_name in self.imports:
                if import_name not in self.used_names:
                    lineno = self._find_import_line(import_name)
                    if lineno:
                        self.unused_imports.append(
                            {
                                "name": import_name,
                                "file": str(self.filepath),
                                "line": lineno,
                                "type": "import",
                            }
                        )

        except SyntaxError:
            pass  # Skip files with syntax errors

    def _find_definition_line(self, name: str, keyword: str) -> Optional[int]:
        """Find line number of definition."""
        pattern = re.compile(rf"^\s*{keyword}\s+{name}\s*[\(:]")
        for i, line in enumerate(self.lines, 1):
            if pattern.match(line):
                return i
        return None

    def _find_import_line(self, name: str) -> Optional[int]:
        """Find line number of import."""
        for i, line in enumerate(self.lines, 1):
            if f"import {name}" in line or f"import.*{name}" in line:
                return i
        return None


def analyze_dead_code(
    root: Path,
    config: HygieneConfig,
    output_path: Optional[Path] = None,
) -> Dict:
    """Analyze repository for dead code."""
    if output_path is None:
        output_path = root / "reports" / "dead_code.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_unused_functions = []
    all_unused_classes = []
    all_unused_imports = []

    # Exclude patterns
    exclude_patterns = config.get(
        "dead_code.exclude_patterns", ["__init__\\.py$", "test_.*\\.py$"]
    )
    exclude_names = config.get(
        "dead_code.exclude_names", ["__all__", "__version__", "main", "cli", "app"]
    )
    ignore_unused_imports = config.get("dead_code.ignore_unused_imports", ["__init__.py"])

    # Scan Python files
    for py_file in root.rglob("*.py"):
        # Skip excluded paths
        if any(
            part.startswith(".")
            or part in ["__pycache__", "venv", ".venv", "node_modules"]
            for part in py_file.parts
        ):
            continue

        # Skip excluded patterns
        rel_path = str(py_file.relative_to(root))
        if any(re.search(pattern, rel_path) for pattern in exclude_patterns):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()

            analyzer = DeadCodeAnalyzer(source, py_file.relative_to(root))
            analyzer.analyze()

            # Filter out excluded names
            for func in analyzer.unused_functions:
                if func["name"] not in exclude_names:
                    all_unused_functions.append(func)

            for cls in analyzer.unused_classes:
                if cls["name"] not in exclude_names:
                    all_unused_classes.append(cls)

            # Filter imports based on file
            if py_file.name not in ignore_unused_imports:
                all_unused_imports.extend(analyzer.unused_imports)

        except Exception:
            continue

    # Generate report
    with open(output_path, "w") as f:
        f.write("# Dead Code Analysis Report\n\n")
        f.write(f"Generated: {Path.cwd()}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Unused functions**: {len(all_unused_functions)}\n")
        f.write(f"- **Unused classes**: {len(all_unused_classes)}\n")
        f.write(f"- **Unused imports**: {len(all_unused_imports)}\n\n")

        if all_unused_functions:
            f.write("## Unused Functions\n\n")
            for func in sorted(all_unused_functions, key=lambda x: x["file"]):
                f.write(f"- `{func['name']}` in [{func['file']}:{func['line']}]({func['file']}#L{func['line']})\n")
            f.write("\n")

        if all_unused_classes:
            f.write("## Unused Classes\n\n")
            for cls in sorted(all_unused_classes, key=lambda x: x["file"]):
                f.write(f"- `{cls['name']}` in [{cls['file']}:{cls['line']}]({cls['file']}#L{cls['line']})\n")
            f.write("\n")

        if all_unused_imports:
            f.write("## Unused Imports\n\n")
            # Group by file
            by_file = defaultdict(list)
            for imp in all_unused_imports:
                by_file[imp["file"]].append(imp)

            for file, imports in sorted(by_file.items()):
                f.write(f"### {file}\n\n")
                for imp in imports:
                    f.write(f"- Line {imp['line']}: `{imp['name']}`\n")
                f.write("\n")

        if not (all_unused_functions or all_unused_classes or all_unused_imports):
            f.write("✓ No dead code detected.\n")

    return {
        "functions": all_unused_functions,
        "classes": all_unused_classes,
        "imports": all_unused_imports,
    }


def main():
    """CLI entry point for dead code analysis."""
    root = Path.cwd()
    config = HygieneConfig()

    print("🔍 Analyzing dead code...")
    results = analyze_dead_code(root, config)

    print(f"   Found {len(results['functions'])} unused functions")
    print(f"   Found {len(results['classes'])} unused classes")
    print(f"   Found {len(results['imports'])} unused imports")
    print()
    print("✓ Analysis complete")
    print("  - reports/dead_code.md")


if __name__ == "__main__":
    main()
