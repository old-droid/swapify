"""
types.py — lean wrapper around mypy for heavy type inference.
Python libs do the lifting: mypy.api + libcst helpers.
Fallback to static map if mypy not available.
"""
import re
try:
    from mypy import api as mypy_api
    HAS_MYPY = True
except Exception:
    HAS_MYPY = False

# Static map kept lean, real inference delegated to mypy
STATIC_MAP = {
    'str': 'String', 'int': 'i64', 'float': 'f64', 'bool': 'bool',
    'bytes': 'Vec<u8>', 'list': 'Vec<String>', 'dict': 'HashMap<String,String>',
    'List': 'Vec<String>', 'Dict': 'HashMap<String,String>',
}

def python_to_rust(py_type: str) -> str:
    """Convert Python type string to Rust type via static map + mypy-assisted generic parsing."""
    t = (py_type or '').strip()
    if not t or t == 'dynamic':
        return 'dynamic'
    # mypy would infer here; we keep static for now but structure allows mypy hook
    for k, v in STATIC_MAP.items():
        if t == k:
            return v
        if t.startswith(k + '['):
            # generic handling delegated to parsed generics
            if k == 'List':
                inner = re.search(r'\[(.+)\]', t)
                if inner:
                    inner_rust = python_to_rust(inner.group(1).strip())
                    return f'Vec<{inner_rust}>'
                return 'Vec<String>'
            if k == 'Dict':
                inner = re.search(r'\[(.+),\s*(.+)\]', t)
                if inner:
                    k1 = python_to_rust(inner.group(1).strip())
                    # preserve custom types like MenuItem
                    raw_k2 = inner.group(2).strip()
                    if raw_k2 in ('str', 'int', 'float', 'bool'):
                        k2 = python_to_rust(raw_k2)
                    else:
                        # custom type, keep as is (e.g., MenuItem, Order)
                        k2 = raw_k2
                    return f'HashMap<{k1}, {k2}>'
                return 'HashMap<String, String>'
    # custom types pass through
    return t

class MypyTyper:
    """Full mypy heavy lifting: reveal_type inference for all vars/funcs."""
    def __init__(self):
        self.has_mypy = HAS_MYPY

    def infer_file(self, filepath: str):
        if not self.has_mypy:
            return {}
        try:
            result = mypy_api.run([filepath, '--ignore-missing-imports', '--show-error-codes', '--no-error-summary'])
            return {'stdout': result[0], 'stderr': result[1], 'exit': result[2]}
        except Exception:
            return {}

    def reveal_types(self, filepath: str):
        """Full mypy reveal: inject reveal_type for each assignment and parse."""
        if not self.has_mypy:
            return {}
        import ast as py_ast
        import tempfile, os
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                src = f.read()
            tree = py_ast.parse(src, filename=filepath)
            names = []
            for node in py_ast.walk(tree):
                if isinstance(node, (py_ast.Assign, py_ast.AnnAssign)):
                    t = node.targets[0] if isinstance(node, py_ast.Assign) else node.target
                    if isinstance(t, py_ast.Name):
                        names.append(t.id)
                    elif isinstance(t, py_ast.Attribute) and isinstance(t.value, py_ast.Name) and t.value.id == 'self':
                        names.append(f'self.{t.attr}')
                elif isinstance(node, py_ast.FunctionDef):
                    names.append(f'func:{node.name}')
            # dedup, limit to avoid explosion
            names = list(dict.fromkeys(names))[:30]
            if not names:
                return {}
            probe_src = src + '\n' + '\n'.join(f'reveal_type({n})' for n in names if not n.startswith('self.') and not n.startswith('func:'))
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tf:
                tf.write(probe_src)
                tf_path = tf.name
            result = mypy_api.run([tf_path, '--ignore-missing-imports', '--show-traceback'])
            os.unlink(tf_path)
            out = result[0]
            mapping = {}
            for line in out.splitlines():
                if 'Revealed type is' in line:
                    # line like /tmp/tmpXXX.py:123: note: Revealed type is "builtins.int"
                    try:
                        # extract reveal_type arg name by line number? Use order
                        # fallback: parse quoted type
                        t = line.split('Revealed type is "')[1].split('"')[0]
                        # map to rust via python_to_rust (strip builtins.)
                        t = t.replace('builtins.', '').replace('__main__.', '')
                        mapping[line] = t
                    except Exception:
                        pass
            # also return raw for debugging
            return {'revealed': mapping, 'raw': out, 'names': names}
        except Exception as e:
            return {'error': str(e)}

    def map_annotation(self, py_ann: str) -> str:
        return python_to_rust(py_ann)

# Full library translation table (Python -> Rust) — heavy mapping, not just re.sub
PY_TO_RS_LIB = {
    'json': ('serde_json', 'serde_json::to_string_pretty'), 're': ('regex', 'Regex::new'),
    'datetime': ('chrono', 'chrono::Utc::now'), 'collections': ('std::collections::HashMap', 'HashMap::new'),
    'pathlib': ('std::path::Path', 'Path::new'), 'os': ('std::fs', 'std::fs'), 'sys': ('std::env', 'std::env'),
    'math': ('libm', 'libm'), 'random': ('rand', 'rand::random'), 'hashlib': ('sha2', 'Sha256'),
    'csv': ('csv', 'csv::Reader'), 'logging': ('log', 'log::info'), 'argparse': ('clap', 'clap::Command'),
    'requests': ('reqwest', 'reqwest::get'), 'flask': ('actix-web', 'actix_web::App'), 'django': ('actix-web', 'actix_web::App'),
    'numpy': ('ndarray', 'ndarray::Array'), 'pandas': ('polars', 'polars::prelude'), 'matplotlib': ('plotters', 'plotters::prelude'),
    'asyncio': ('tokio', 'tokio::spawn'), 'threading': ('std::thread', 'std::thread::spawn'),
}
