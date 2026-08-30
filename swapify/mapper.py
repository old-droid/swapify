import requests

CRATE_API = "https://crates.io/api/v1/crates"
DEFAULT_MAP = {
    'numpy': 'ndarray', 'pandas': 'polars', 'requests': 'reqwest', 'flask': 'actix-web',
    'django': 'actix-web', 'matplotlib': 'plotters', 'sklearn': 'linfa', 'json': 'serde_json',
    'os': 'std::fs', 'sys': 'std::env', 'collections': 'std::collections', 'pathlib': 'std::path',
    'datetime': 'chrono', 're': 'regex', 'math': 'libm', 'random': 'rand', 'sqlite3': 'rusqlite',
    'subprocess': 'std::process', 'asyncio': 'tokio', 'threading': 'std::thread', 'csv': 'csv',
    'logging': 'log', 'argparse': 'clap', 'pickle': 'serde', 'hashlib': 'sha2', 'hmac': 'hmac',
    'base64': 'base64', 'urllib': 'url', 'glob': 'glob', 'shutil': 'std::fs', 'tempfile': 'tempfile',
    'decimal': 'bigdecimal', 'statistics': 'statrs', 'xml': 'quick-xml', 'email': 'lettre',
    'http': 'hyper', 'socket': 'tokio', 'ssl': 'native-tls', 'uuid': 'uuid', 'enum': 'strum',
    'typing': '', 'typing_extensions': '', 'abc': '', 'copy': '', 'functools': '', 'itertools': '',
    'unittest': '', 'io': '', 'time': '', 'operator': '',
}
STD_CRATES = {'std::fs', 'std::env', 'std::path', 'std::collections', 'std::process', 'std::thread'}
# crates that should never become dependencies (stdlib noise)
EXCLUDE_CRATES = {'typing', 'typing_extensions', 'typing-extensions'}
# known good versions for generated Cargo.toml
CRATE_VERSIONS = {
    'serde_json': '1.0', 'chrono': '0.4', 'regex': '1', 'rand': '0.8',
    'tokio': '1', 'reqwest': '0.11', 'polars': '0.40', 'ndarray': '0.15',
    'actix-web': '4', 'plotters': '0.3', 'linfa': '0.7', 'rusqlite': '0.30',
    'csv': '1', 'log': '0.4', 'clap': '4', 'sha2': '0.10', 'hmac': '0.12',
    'base64': '0.21', 'url': '2', 'glob': '0.3', 'tempfile': '3',
    'bigdecimal': '0.3', 'statrs': '0.16', 'quick-xml': '0.30', 'lettre': '0.11',
    'hyper': '0.14', 'native-tls': '0.2', 'uuid': '1', 'strum': '0.25',
    'libm': '0.2', 'serde': '1.0',
}


class LibraryMapper:
    def __init__(self, use_api=True):
        self.use_api = use_api
        self.custom = dict(DEFAULT_MAP)

    def map_library(self, lib_name):
        if not lib_name:
            return {'crate': '', 'note': ''}
        key = lib_name.lower().split('.')[0]
        if key in self.custom:
            return {'crate': self.custom[key], 'note': ''}
        if self.use_api:
            return self._search(key)
        return {'crate': '', 'note': 'unknown'}

    def _search(self, q):
        try:
            r = requests.get(CRATE_API, params={'q': q, 'per_page': 1}, timeout=3, headers={'User-Agent': 'swapify/0.1'})
            if r.status_code == 200:
                j = r.json()
                crates = j.get('crates', [])
                if crates:
                    return {'crate': crates[0]['name'], 'note': crates[0].get('description', '')[:60]}
        except Exception:
            pass
        return {'crate': '', 'note': 'not found'}

    def map_imports(self, imports):
        out = []
        for imp in imports:
            if imp['type'] == 'import':
                for n in imp['names']:
                    out.append({'import': n, **self.map_library(n)})
            else:
                mod = imp['module'] or ''
                out.append({'import': mod, 'names': imp['names'], **self.map_library(mod)})
        return out

    def add_mapping(self, py_lib, crate, note=''):
        self.custom[py_lib] = crate

    def get_cargo_deps(self, mappings):
        deps = []
        for m in mappings:
            c = m.get('crate', '')
            if not c or c in STD_CRATES or '::' in c or c in EXCLUDE_CRATES:
                continue
            # normalize: serde_json already correct, but crate names from API may have dashes
            if c in CRATE_VERSIONS or '-' not in c:
                deps.append({'name': c, 'import': m.get('import', c)})
        seen = {}
        for d in deps:
            seen[d['name']] = d
        return list(seen.values())

    def get_crate_version(self, name):
        return CRATE_VERSIONS.get(name, "0.1")
