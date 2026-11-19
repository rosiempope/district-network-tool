import ast
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "dhc"

# Inner rings must never import from outer rings.
FORBIDDEN = {
    "domain": ["dhc.use_cases", "dhc.adapters", "dhc.app", "streamlit", "pandas", "pandapipes"],
    "use_cases": ["dhc.adapters", "dhc.app", "streamlit", "pandapipes"],
    "adapters": ["dhc.app", "streamlit"],
}


def imported_modules(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_dependency_rule():
    problems = []
    for ring, banned in FORBIDDEN.items():
        ring_path = SRC / ring
        assert ring_path.is_dir(), f"Expected folder missing: {ring_path}"
        for file in ring_path.rglob("*.py"):
            for module in imported_modules(file):
                if any(module == b or module.startswith(b + ".") for b in banned):
                    problems.append(f"{file.relative_to(SRC)} imports {module}")
    assert not problems, "\n".join(problems)