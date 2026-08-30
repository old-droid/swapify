"""
variables.py — lean wrapper around jedi for variable logic.
Heavy lifting: jedi.Script for inference, goto, completions.
"""
import re

try:
    import jedi
    HAS_JEDI = True
except Exception:
    HAS_JEDI = False

# Fallback type map (used when jedi not available)
STATIC_VAR_MAP = {
    'int': 'i64', 'float': 'f64', 'str': 'String', 'bool': 'bool',
    'list': 'Vec<String>', 'dict': 'HashMap<String,String>',
}

class VariableTracker:
    """jedi does the work, this is a thin facade."""
    def __init__(self):
        self.has_jedi = HAS_JEDI

    def infer_type(self, filepath: str, var_name: str, source: str = None) -> str:
        """Infer Rust type for a Python variable via jedi."""
        if not self.has_jedi or not filepath:
            return 'String'
        try:
            # jedi heavy lifting: infer type from file
            script = jedi.Script(path=filepath)
            # find all occurrences of var_name, infer
            # jedi's infer() gives Python type, we map to Rust
            for line_no, line in enumerate(open(filepath, encoding='utf-8', errors='replace').read().splitlines(), 1):
                if var_name in line and '=' in line:
                    # use jedi to get completions/types at that line
                    try:
                        # column of var_name
                        col = line.index(var_name) + len(var_name)
                        inferred = script.infer(line_no, col)
                        for inf in inferred:
                            t = inf.name  # e.g. 'int', 'str', 'list'
                            if t in STATIC_VAR_MAP:
                                return STATIC_VAR_MAP[t]
                            # jedi gives 'int' for 0, 'str' for "a", etc.
                            if 'int' in t: return 'i64'
                            if 'float' in t: return 'f64'
                            if 'str' in t: return 'String'
                            if 'bool' in t: return 'bool'
                            if 'list' in t: return 'Vec<String>'
                            if 'dict' in t: return 'HashMap<String,String>'
                    except Exception:
                        pass
        except Exception:
            pass
        # fallback: regex on source value
        if source:
            v = source.strip()
            if re.match(r'^-?\d+$', v): return 'i64'
            if re.match(r'^-?\d+\.\d+$', v): return 'f64'
            if v.startswith('"') or v.startswith("'"): return 'String'
            if v in ('True','False'): return 'bool'
            if v.startswith('['): return 'Vec<String>'
            if v.startswith('{'): return 'HashMap<String,String>'
        return 'String'

    def track_file(self, filepath: str) -> dict:
        """Track all variables in file via jedi.names()"""
        if not self.has_jedi:
            return {}
        try:
            script = jedi.Script(path=filepath)
            names = script.get_names(all_scopes=True, definitions=True, references=True)
            out = {}
            for n in names:
                if n.type in ('statement', 'param'):
                    out[n.name] = {'type': n.type, 'line': n.line, 'is_variable': n.is_side_effect()}
            return out
        except Exception:
            return {}

    def is_mutated(self, var_name: str, source: str) -> bool:
        """Check if variable is mutated (needs mut) via jedi + regex."""
        # jedi could do goto, but simple regex is enough for lean wrapper
        # heavy lifting is still jedi's parsing, we just query
        pattern = rf'\b{re.escape(var_name)}\s*(=|\+=|-=|\.push|\.insert|\.append)'
        return bool(re.search(pattern, source))

# singleton for converter to use
tracker = VariableTracker()
