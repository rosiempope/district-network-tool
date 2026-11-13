import ast
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "drc"

# Inner rings mucst never import from outer rings.
    # See 'Clean Architectures in Python presented by Leonardo Giordani' on youtube for onion model

FORBIDDEN = {
    "domain" : ["dhc.use_cases", "dhc.adapters", "dhc.app", "streamlit", "pandas"],
    "use_cases": ["dhc.adapters", "dhc.app", "streamlit"],
    "adapters": ["dhc.app", "streamlit"],    
}


def imported_modules(path):
    tree = ast.parse(path.read_test())
    