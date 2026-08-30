import os
import sys
from .parser import Parser
from .mapper import LibraryMapper
from .converter import RustConverter

class SwapifyCLI:
    def __init__(self):
        self.parser = Parser()
        self.mapper = LibraryMapper()
        self.converter = RustConverter(self.mapper)

    def run(self, target_dir):
        if not target_dir or not os.path.isdir(target_dir):
            print('Error: "{}" is not a valid directory'.format(target_dir), file=sys.stderr)
            print('Usage: swap <directory>', file=sys.stderr)
            sys.exit(1)
        py_files = self._find_py_files(target_dir)
        if not py_files:
            print('No Python files found in {}'.format(target_dir))
            sys.exit(0)
        cargo_deps = []
        converted, failed = 0, 0
        for fp in py_files:
            print('Converting: {}'.format(fp))
            try:
                parsed = self.parser.parse_file(fp)
            except Exception as e:
                print('  ! parse error: {}'.format(e), file=sys.stderr)
                failed += 1
                continue
            if parsed.get('error'):
                print('  ! {}: {}'.format(os.path.basename(fp), parsed['error']), file=sys.stderr)
                # still emit stub so Cargo.toml isn't empty
                parsed['imports'] = parsed.get('imports', [])
            try:
                mappings = self.mapper.map_imports(parsed.get('imports', []))
                cargo_deps.extend(self.mapper.get_cargo_deps(mappings))
                rust = self.converter.convert(parsed)
                out = self._rust_path(fp, target_dir)
                os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
                with open(out, 'w', encoding='utf-8') as f:
                    f.write(rust)
                print('  -> {}'.format(out))
                converted += 1
            except Exception as e:
                print('  ! convert failed: {}'.format(e), file=sys.stderr)
                failed += 1
        try:
            self._write_cargo(target_dir, cargo_deps)
            self._write_readme(target_dir)
        except Exception as e:
            print('  ! write Cargo.toml failed: {}'.format(e), file=sys.stderr)
        print('\nDone. {} converted, {} failed.'.format(converted, failed))
        print('Cargo.toml with {} deps.'.format(len(set(d['name'] for d in cargo_deps)) if cargo_deps else 0))
        if failed:
            sys.exit(2)

    def _find_py_files(self, d):
        out = []
        for root, _, files in os.walk(d):
            # skip hidden, __pycache__, venv, target
            if any(x in root for x in ('__pycache__', '.git', 'venv', '.venv', 'target', '.mypy')):
                continue
            for f in files:
                if f.endswith('.py'):
                    out.append(os.path.join(root, f))
        return sorted(out)

    def _rust_path(self, py, base):
        rel = os.path.relpath(py, base)
        base_no_ext, _ = os.path.splitext(rel)
        return os.path.join(base, base_no_ext + '.rs')

    def _write_cargo(self, d, deps):
        seen = {}
        for dep in deps:
            seen[dep['name']] = dep['name']
        path = os.path.join(d, 'Cargo.toml')
        if os.path.exists(path):
            print('  Cargo.toml exists, skipping overwrite -> {}'.format(path))
            return
        lines = ['[package]', 'name = "swapified"', 'version = "0.1.0"', 'edition = "2021"', '', '[dependencies]']
        for n in sorted(seen):
            lines.append('{} = "0.1"'.format(n))
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    def _write_readme(self, d):
        p = os.path.join(d, 'README.md')
        if os.path.exists(p):
            return
        with open(p, 'w', encoding='utf-8') as f:
            f.write('# Swapified\n\nConverted by Swapify. Review before `cargo build`.\n')

def main():
    if len(sys.argv) < 2:
        print('Usage: swap <directory>', file=sys.stderr)
        sys.exit(1)
    SwapifyCLI().run(sys.argv[1])

if __name__ == '__main__':
    main()
