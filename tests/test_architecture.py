import ast
# what this does is read the imports in the listed folders and checks if
# there is cicurlarity dependencies all the follow the onion model.
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "dhc"

# Inner rings mucst never import from outer rings.
    # See 'Clean Architectures in Python presented by Leonardo Giordani' on youtube for onion model

FORBIDDEN = {
    "domain" : ["dhc.use_cases", "dhc.adapters", "dhc.app", "streamlit", "pandas"],
    "use_cases": ["dhc.adapters", "dhc.app", "streamlit"],
    "adapters": ["dhc.app", "streamlit"],    
}


def imported_modules(path):
    #Defines a function that takes a file path and gives back the names of everything that file imports.
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            #isinstance checks what type of thing the node is.
            for alias in node.names:
                yield alias.name
                #One import line can bring in several things (import numpy, pandas). node.names holds each of them, so we loop over them and give back each name
        elif isinstance(node, ast.ImportFrom) and node.module:
            #ast.ImportFrom is the second style, from dhc.domain.config import Site, which Python treats as a different kind of node than a plain import
            yield node.module
            #so use yield vs return when you have a cascade of answers you dont know how many iterations of them are.

def test_dependency_rule():
    #Pytest automatically runs any function whose name starts with test_. That naming is how it finds your tests.
    problems = []
    for ring, banned in FORBIDDEN.items():
        ring_path = SRC / ring
        for file in (SRC/ring).rglob("*.py"):
            for module in imported_modules(file):
                if any(module == b or module.startswith(b + ".") for b in banned):
                    problems.append(f"{file.relative_to(SRC)} imports {module}")
    assert not problems, "\n".join(problems)
