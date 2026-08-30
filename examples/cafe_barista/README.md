# Cafe Barista — Python → Rust via `swap`

Original Python: `cafe_barista.py` (219 lines) — classes `MenuItem`, `Order`, `Barista`, `Cafe`.

```bash
swap ./examples/cafe_barista
# raw output -> cafe_barista.swap.rs (269 lines, 17 rustc errors)
# fixed port -> src/main.rs (compiles, runs)
```

## Raw swap bugs (before fix)

`swapify/converter.py:195` generated:

- `swap.rs:10` `f"${price:.2f}"` left as Python f-string
- `swap.rs:14` `or` not `||`, `swap.rs:25` `not re.match`
- `swap.rs:67` ternary `"available" if cond else "out"`
- `swap.rs:50` all fields `String` (price f64 lost)
- `swap.rs:90` `self.items: List[str] = []` Python syntax left
- `swap.rs:7` `use typing;` + Cargo `typing="0.1"` (crates.io noise)
- `swap.rs:267` `MENU` -> `Default::default()`
- `swap.rs:32` `Cafe(SHOP_NAME)` missing `::new`

`rustc cafe_barista.swap.rs` → 17 errors.

## Fixes pushed

- `mapper.py:11` exclude `typing`, add `CRATE_VERSIONS` + `get_crate_version`
- `cli.py:75` Cargo `serde_json="1.0", chrono="0.4", regex="1"`
- `converter.py:78` `use regex::Regex`, `converter.py:386` f-string→`format!`, `converter.py:428` `or→||`, `and→&&`, `in→contains_key`, `converter.py:210` fields with types via `arg_types` + `_py_ann_to_rust`, `converter.py:137` `&mut self` detection, `converter.py:284` `MENU` → `LazyLock<HashMap>`, `converter.py:350` `[a,b]→vec![...]`

After fix:

```bash
swap /tmp/cafe_test -> 3 deps (chrono 0.4, regex 1, serde_json 1.0), 0 typing
cargo check -> warnings only (vs 17 errors)
```

## Run

```bash
python3 examples/cafe_barista/cafe_barista.py
cargo run --manifest-path examples/cafe_barista/Cargo.toml
# both: Total $14.04, Revenue $14.04, [valid name]
```

Fixed port is `src/main.rs` (HashMap, LazyLock, format!, borrow-checked).

Raw swap preserved as `cafe_barista.swap.rs` for reference.
