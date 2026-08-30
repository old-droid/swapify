# Swapify — Python to Rust Converter

Swap Python to Rust in one command.

```bash
swap <directory>
```

Modular,  uses Python `ast` + `re` and live lookup on `crates.io` for library mapping.

## Install

```bash
pip install -e .   # exposes `swap` CLI
```

or

```bash
pip install swapify
```

## Usage

```bash
swap ./my_python_project
# Converts every .py -> .rs side-by-side, writes Cargo.toml + README.md
```

Example:

```bash
swap /tmp/battle
cat /tmp/battle/src/main.rs
cat /tmp/battle/Cargo.toml
```

## How it works

| Module | Role | Technique |
|---|---|---|
| `swapify/parser.py` | Parse Python files, extract imports / functions / classes / vars | `ast.parse`, `ast.unparse`, `re.findall` |
| `swapify/mapper.py` | Map Python libs → Rust crates | Static map + `https://crates.io/api/v1/crates?q=...` |
| `swapify/converter.py` | Emit Rust code | Regex transforms, collects, brace balancing |
| `swapify/cli.py` | CLI, file discovery, Cargo.toml generation | `os.walk`, `argparse`-style |

Default mapping (excerpt):

`numpy→ndarray`, `pandas→polars`, `requests→reqwest`, `flask/django→actix-web`, `matplotlib→plotters`, `datetime→chrono`, `re→regex`, `random→rand`, `asyncio→tokio`, etc. Unknown libs are looked up live on crates.io, fallback is graceful offline.

## Generated output

- `use` statements for each crate
- `fn` with `&str` / `i64` / `f64` / `String` types inferred from annotations
- `struct` + `impl` for classes (`__init__` → `pub fn new() -> Self`)
- `println!`, `.len()`, `.push()`, `HashMap::new()`, `String::from` via regex
- `const` for module globals, `Cargo.toml` with `edition = "2021"`

All control flow (`for`/`while`/`if`/`elif`/`else`) is handled via regex and brace-balanced, multiline `ast.unparse` blocks are split on `\n` without flattening.

## Battle-tested

- `utf-8` with `errors=replace`, handles `SyntaxError`, `AnnAssign`, non-utf8 files
- Skips `__pycache__`, `.git`, `venv`, `target`
- `Cargo.toml` never overwritten, `README.md` idempotent
- Network timeout 3s, `User-Agent: swapify/0.1`, offline degrades gracefully
- Exit codes: `0` no files / `1` bad dir / `2` partial failures

## Project layout

```
swapify/
  parser.py      # AST extraction
  mapper.py      # crates.io lookup
  converter.py   # Python → Rust
  cli.py         # swap entry
setup.py
README.md
```



## License

MIT
