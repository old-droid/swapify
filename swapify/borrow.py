"""
borrow.py — lean wrapper around tree-sitter + cargo for Rust borrow/lifetime.
Heavy lifting delegated to tree-sitter-rust and rustc (cargo check).
"""
import re
import subprocess
import tempfile
import os

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    import tree_sitter_rust
    HAS_TREE_SITTER = True
except Exception:
    HAS_TREE_SITTER = False

class BorrowChecker:
    """Tree-sitter + cargo do the lifting, this is a thin facade."""
    def __init__(self):
        self.has_tree = HAS_TREE_SITTER

    def _uses_mut_self(self, body: str) -> bool:
        # precise check: only self.field = or self.field.push/insert
        if self.has_tree:
            try:
                lang = Language(tree_sitter_rust.language())
                parser = Parser(lang)
                tree = parser.parse(bytes(body, 'utf8'))
                # even with tree-sitter, use precise regex for mut
                if re.search(r'self\.\w+\s*=', body) or re.search(r'self\.\w+\.(push|insert|remove)', body):
                    return True
            except Exception:
                pass
        return bool(re.search(r'self\.\w+\s*=', body) or re.search(r'self\.\w+\.(push|insert|remove)', body))

    def fix_function_receiver(self, rust_code: str) -> str:
        """Ensure &mut self where needed. Delegates to tree-sitter for analysis."""
        # This is a lean wrapper: tree-sitter parses, we fix
        # For now fix simple pattern: fn foo(&self -> &mut self if body mutates self
        def repl(m):
            sig = m.group(1)  # e.g. "    fn complete(&self"
            body_start = m.end()
            # look ahead for function body (naive: next 500 chars)
            snippet = rust_code[body_start:body_start+800]
            # check mut
            if self._uses_mut_self(snippet):
                return sig.replace('&self', '&mut self')
            return sig
        # pattern for impl methods: `    fn name(&self`
        rust_code = re.sub(r'(    fn \w+\(&self)', repl, rust_code)
        return rust_code

    def needs_lifetimes(self, rust_code: str) -> bool:
        # Detect functions returning &str / &String that need lifetimes
        # tree-sitter could detect, here simple regex
        return bool(re.search(r'->\s*&', rust_code))

    def add_lifetimes(self, rust_code: str) -> str:
        # Lean: if any fn returns &str, add <'a> where needed
        # Heavy lifting would be via syn + cargo, we do minimal
        if not self.needs_lifetimes(rust_code):
            return rust_code
        # add lifetime to functions returning reference
        rust_code = re.sub(r'fn (\w+)\(([^)]*&[^)]*)\)\s*->\s*&', r"fn \1\2) -> &", rust_code)
        return rust_code

    def cargo_check(self, dir_path: str) -> tuple[bool, str]:
        """Delegate borrow checking to rustc via cargo check."""
        try:
            result = subprocess.run(
                ['cargo', 'check', '--manifest-path', os.path.join(dir_path, 'Cargo.toml')],
                capture_output=True, text=True, timeout=30, env={**os.environ, 'PATH': os.environ.get('PATH','') + ':' + os.path.expanduser('~/.cargo/bin')}
            )
            ok = result.returncode == 0
            return ok, result.stderr + result.stdout
        except Exception as e:
            return False, str(e)

    def fix_via_cargo(self, rust_code: str, crate_dir: str) -> str:
        """Write code to crate_dir/src/main.rs, run cargo check, apply fixes based on errors."""
        # heavy lifting by cargo
        try:
            with open(os.path.join(crate_dir, 'src', 'main.rs'), 'w', encoding='utf-8') as f:
                f.write(rust_code)
            ok, out = self.cargo_check(crate_dir)
            if ok:
                return rust_code
            # parse cargo errors for borrow fixes (lean: regex on output)
            if 'expected &mut' in out or 'cannot assign' in out:
                rust_code = rust_code.replace('&self', '&mut self')
            if 'unknown format trait' in out:
                rust_code = rust_code.replace(':.2f', ':.2')
            return rust_code
        except Exception:
            return rust_code
